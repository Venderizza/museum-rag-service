import asyncio
import dramatiq
from app.application.services.chunking_service import ChunkingService
from app.domain.enums import DocumentStatus
from app.application.use_cases.index_document import IndexDocumentUseCase
from app.config.settings import get_settings
from app.infrastructure.db.repositories.chunk_repository import PostgresChunkRepository
from app.infrastructure.db.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.db.session import AsyncSessionFactory
from app.infrastructure.embeddings.gigachat_provider import GigaChatEmbeddingProvider
from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from app.infrastructure.gigachat.auth import GigaChatAuthClient
from app.infrastructure.qdrant.vector_store import QdrantVectorStore
from app.infrastructure.queue.broker import broker  # noqa: F401 ensures broker is registered


@dramatiq.actor(max_retries=3)
def index_document_task(document_id: int) -> None:
    asyncio.run(_index_document(document_id))


async def _index_document(document_id: int) -> None:
    settings = get_settings()
    async with AsyncSessionFactory() as session:
        try:
            if settings.embedding_provider == 'gigachat':
                auth_client = GigaChatAuthClient(
                    auth_url=settings.gigachat_auth_url,
                    scope=settings.gigachat_scope,
                    authorization_key=settings.gigachat_authorization_key,
                    client_id=settings.gigachat_client_id,
                    client_secret=settings.gigachat_client_secret,
                    verify_ssl=settings.gigachat_verify_ssl,
                )
                embedding_provider = GigaChatEmbeddingProvider(
                    api_url=settings.gigachat_api_url,
                    auth_client=auth_client,
                    model=settings.gigachat_embedding_model,
                    dimension=settings.embedding_dimension,
                    version=settings.embedding_version,
                    verify_ssl=settings.gigachat_verify_ssl,
                )
            else:
                embedding_provider = MockEmbeddingProvider(
                    settings.embedding_dimension,
                    settings.embedding_model_name,
                    settings.embedding_version,
                )
            use_case = IndexDocumentUseCase(
                documents=PostgresDocumentRepository(session),
                chunks=PostgresChunkRepository(session),
                vector_store=QdrantVectorStore(settings.qdrant_host, settings.qdrant_port, settings.qdrant_collection),
                embedding_provider=embedding_provider,
                chunking_service=ChunkingService(settings.chunk_size_tokens, settings.chunk_overlap_tokens),
            )
            await use_case.execute(document_id)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            await _mark_indexing_failed(document_id, str(exc))
            raise


async def _mark_indexing_failed(document_id: int, error: str) -> None:
    async with AsyncSessionFactory() as session:
        repository = PostgresDocumentRepository(session)
        await repository.set_status(document_id, DocumentStatus.FAILED)
        await repository.set_indexing_error(document_id, error)
        await session.commit()

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.services.chunking_service import ChunkingService
from app.application.services.confidence_service import ConfidenceService
from app.application.services.prompt_builder import PromptBuilder
from app.application.use_cases.add_document import AddDocumentUseCase
from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.application.use_cases.get_document_status import GetDocumentStatusUseCase
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.application.use_cases.reindex_document import ReindexDocumentUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.config.settings import Settings, get_settings
from app.domain.ports.embedding_provider import EmbeddingProvider
from app.domain.ports.llm_provider import LLMProvider
from app.infrastructure.db.repositories.chunk_repository import PostgresChunkRepository
from app.infrastructure.db.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.db.repositories.query_log_repository import PostgresQueryLogRepository
from app.infrastructure.db.session import get_session
from app.infrastructure.embeddings.gigachat_provider import GigaChatEmbeddingProvider
from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from app.infrastructure.gigachat.auth import GigaChatAuthClient
from app.infrastructure.llm.gigachat_provider import GigaChatLLMProvider
from app.infrastructure.llm.mock_provider import MockLLMProvider
from app.infrastructure.llm.openai_compatible_provider import OpenAICompatibleLLMProvider
from app.infrastructure.qdrant.vector_store import QdrantVectorStore
from app.infrastructure.queue.job_queue import DramatiqJobQueue


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


def _get_gigachat_auth_client(settings: Settings) -> GigaChatAuthClient:
    return GigaChatAuthClient(
        auth_url=settings.gigachat_auth_url,
        scope=settings.gigachat_scope,
        authorization_key=settings.gigachat_authorization_key,
        client_id=settings.gigachat_client_id,
        client_secret=settings.gigachat_client_secret,
        verify_ssl=settings.gigachat_verify_ssl,
    )


def get_embedding_provider(settings: Settings = Depends(get_settings)) -> EmbeddingProvider:
    if settings.embedding_provider == 'gigachat':
        return GigaChatEmbeddingProvider(
            api_url=settings.gigachat_api_url,
            auth_client=_get_gigachat_auth_client(settings),
            model=settings.gigachat_embedding_model,
            dimension=settings.embedding_dimension,
            version=settings.embedding_version,
            verify_ssl=settings.gigachat_verify_ssl,
        )
    return MockEmbeddingProvider(settings.embedding_dimension, settings.embedding_model_name, settings.embedding_version)


def get_llm_provider(settings: Settings = Depends(get_settings)) -> LLMProvider:
    if settings.llm_provider == 'gigachat':
        return GigaChatLLMProvider(
            api_url=settings.gigachat_api_url,
            auth_client=_get_gigachat_auth_client(settings),
            model=settings.gigachat_model,
            verify_ssl=settings.gigachat_verify_ssl,
        )
    if settings.llm_provider == 'openai_compatible':
        return OpenAICompatibleLLMProvider(settings.openai_compatible_api_url, settings.openai_compatible_api_key, settings.openai_compatible_model)
    return MockLLMProvider()


def get_vector_store(settings: Settings = Depends(get_settings)) -> QdrantVectorStore:
    return QdrantVectorStore(settings.qdrant_host, settings.qdrant_port, settings.qdrant_collection)


def get_add_document_use_case(session: AsyncSession = Depends(get_db_session)) -> AddDocumentUseCase:
    return AddDocumentUseCase(PostgresDocumentRepository(session), DramatiqJobQueue())


def get_status_use_case(session: AsyncSession = Depends(get_db_session)) -> GetDocumentStatusUseCase:
    return GetDocumentStatusUseCase(PostgresDocumentRepository(session), PostgresChunkRepository(session))


def get_delete_use_case(session: AsyncSession = Depends(get_db_session), vector_store: QdrantVectorStore = Depends(get_vector_store)) -> DeleteDocumentUseCase:
    return DeleteDocumentUseCase(PostgresDocumentRepository(session), PostgresChunkRepository(session), vector_store)


def get_reindex_use_case(session: AsyncSession = Depends(get_db_session), vector_store: QdrantVectorStore = Depends(get_vector_store)) -> ReindexDocumentUseCase:
    return ReindexDocumentUseCase(PostgresDocumentRepository(session), PostgresChunkRepository(session), vector_store, DramatiqJobQueue())


def get_search_use_case(
    session: AsyncSession = Depends(get_db_session),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> SearchDocumentsUseCase:
    return SearchDocumentsUseCase(PostgresDocumentRepository(session), vector_store, embedding_provider)


def get_query_use_case(
    session: AsyncSession = Depends(get_db_session),
    search: SearchDocumentsUseCase = Depends(get_search_use_case),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_settings),
) -> QueryDocumentsUseCase:
    return QueryDocumentsUseCase(
        search=search,
        llm_provider=llm_provider,
        query_logs=PostgresQueryLogRepository(session),
        prompt_builder=PromptBuilder(),
        confidence_service=ConfidenceService(settings.retrieval_min_score, settings.answer_confidence_threshold),
        store_prompts=settings.store_llm_prompts,
        store_raw_responses=settings.store_llm_raw_responses,
    )

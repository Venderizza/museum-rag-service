import logging
from app.application.services.chunking_service import ChunkingService
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentNotFoundError
from app.domain.ports.chunk_repository import ChunkRepository
from app.domain.ports.document_repository import DocumentRepository
from app.domain.ports.embedding_provider import EmbeddingProvider
from app.domain.ports.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IndexDocumentUseCase:
    def __init__(
        self,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        chunking_service: ChunkingService,
    ):
        self.documents = documents
        self.chunks = chunks
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.chunking_service = chunking_service

    async def execute(self, document_id: int) -> None:
        document = await self.documents.get_by_document_id(document_id)
        if document is None:
            raise DocumentNotFoundError()
        if document.is_deleted:
            return

        try:
            await self.documents.set_status(document_id, DocumentStatus.PROCESSING)
            await self.documents.set_indexing_error(document_id, None)

            model_name = self.embedding_provider.get_model_name()
            dimension = self.embedding_provider.get_dimension()
            version = self.embedding_provider.get_version()
            chunks = self.chunking_service.split(
                document_id=document_id,
                body=document.body,
                embedding_model_name=model_name,
                embedding_dimension=dimension,
                embedding_version=version,
            )
            texts = [self.chunking_service.build_embedding_text(document.title, chunk.text) for chunk in chunks]
            vectors = await self.embedding_provider.embed_batch(texts)
            await self.vector_store.ensure_collection(dimension)
            await self.chunks.save_many(chunks)
            await self.vector_store.upsert_chunks(chunks, vectors, {document_id: document.title})
            await self.documents.update_embedding_info(document_id, model_name, dimension, version)
            await self.documents.set_status(document_id, DocumentStatus.INDEXED)
            logger.info('Document indexed', extra={'document_id': document_id, 'chunks_count': len(chunks)})
        except Exception:
            # Do not write FAILED status here: after a flush/DB error the SQLAlchemy
            # session may require rollback first. The worker catches the exception,
            # rolls the transaction back, and persists FAILED in a clean transaction.
            logger.exception('Document indexing failed', extra={'document_id': document_id})
            raise

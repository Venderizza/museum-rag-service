import logging
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentAlreadyDeletedError, DocumentNotFoundError
from app.domain.ports.chunk_repository import ChunkRepository
from app.domain.ports.document_repository import DocumentRepository
from app.domain.ports.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DeleteDocumentUseCase:
    def __init__(self, documents: DocumentRepository, chunks: ChunkRepository, vector_store: VectorStore):
        self.documents = documents
        self.chunks = chunks
        self.vector_store = vector_store

    async def execute(self, document_id: int) -> DocumentStatus:
        document = await self.documents.get_by_document_id(document_id)
        if document is None:
            raise DocumentNotFoundError()
        if document.is_deleted:
            raise DocumentAlreadyDeletedError()

        await self.documents.mark_deleted(document_id)
        await self.chunks.mark_deleted_by_document_id(document_id)
        try:
            await self.vector_store.mark_deleted_by_document_id(document_id)
        except Exception:
            logger.exception('Failed to mark vectors deleted; PostgreSQL remains source of truth', extra={'document_id': document_id})
        return DocumentStatus.DELETED

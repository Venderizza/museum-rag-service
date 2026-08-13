from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentDeletedError, DocumentNotFoundError
from app.domain.ports.chunk_repository import ChunkRepository
from app.domain.ports.document_repository import DocumentRepository
from app.domain.ports.job_queue import JobQueue
from app.domain.ports.vector_store import VectorStore


class ReindexDocumentUseCase:
    def __init__(self, documents: DocumentRepository, chunks: ChunkRepository, vector_store: VectorStore, job_queue: JobQueue):
        self.documents = documents
        self.chunks = chunks
        self.vector_store = vector_store
        self.job_queue = job_queue

    async def execute(self, document_id: int) -> DocumentStatus:
        document = await self.documents.get_by_document_id(document_id)
        if document is None:
            raise DocumentNotFoundError()
        if document.is_deleted:
            raise DocumentDeletedError()

        await self.chunks.mark_deleted_by_document_id(document_id)
        await self.vector_store.mark_deleted_by_document_id(document_id)
        await self.documents.set_indexing_error(document_id, None)
        await self.documents.set_status(document_id, DocumentStatus.QUEUED)
        await self.job_queue.enqueue_index_document(document_id)
        return DocumentStatus.QUEUED

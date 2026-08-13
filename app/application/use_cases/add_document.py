from typing import Any
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentAlreadyExistsError
from app.domain.ports.document_repository import DocumentRepository
from app.domain.ports.job_queue import JobQueue


class AddDocumentUseCase:
    def __init__(self, documents: DocumentRepository, job_queue: JobQueue):
        self.documents = documents
        self.job_queue = job_queue

    async def execute(self, *, document_id: int, title: str, body: str, metadata: dict[str, Any]) -> DocumentStatus:
        if await self.documents.exists(document_id):
            raise DocumentAlreadyExistsError()
        await self.documents.create(document_id, title, body, metadata, DocumentStatus.QUEUED)
        await self.job_queue.enqueue_index_document(document_id)
        return DocumentStatus.QUEUED

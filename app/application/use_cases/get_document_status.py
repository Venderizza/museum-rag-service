from dataclasses import dataclass
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentNotFoundError
from app.domain.ports.chunk_repository import ChunkRepository
from app.domain.ports.document_repository import DocumentRepository


@dataclass(slots=True)
class DocumentStatusResult:
    document_id: int
    status: DocumentStatus
    chunks_count: int
    error: str | None


class GetDocumentStatusUseCase:
    def __init__(self, documents: DocumentRepository, chunks: ChunkRepository):
        self.documents = documents
        self.chunks = chunks

    async def execute(self, document_id: int) -> DocumentStatusResult:
        document = await self.documents.get_by_document_id(document_id)
        if document is None:
            raise DocumentNotFoundError()
        chunks_count = await self.chunks.count_by_document_id(document_id)
        return DocumentStatusResult(document_id=document_id, status=document.status, chunks_count=chunks_count, error=document.indexing_error)

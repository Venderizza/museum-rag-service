from app.domain.entities.source import Source
from app.domain.ports.document_repository import DocumentRepository
from app.domain.ports.embedding_provider import EmbeddingProvider
from app.domain.ports.vector_store import VectorStore


class SearchDocumentsUseCase:
    def __init__(self, documents: DocumentRepository, vector_store: VectorStore, embedding_provider: EmbeddingProvider):
        self.documents = documents
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    async def execute(self, query: str, top_k: int) -> list[Source]:
        vector = await self.embedding_provider.embed_text(query)
        raw_sources = await self.vector_store.search(vector, top_k=top_k, filters={'is_deleted': False})
        active_documents = await self.documents.get_active_by_ids(list({source.document_id for source in raw_sources}))
        active_ids = {document.document_id for document in active_documents}
        return [source for source in raw_sources if source.document_id in active_ids]

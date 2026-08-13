from __future__ import annotations

from typing import Any

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.domain.entities.source import Source
from app.domain.enums import DocumentStatus, QueryStatus
from app.domain.ports.llm_provider import LLMResponse


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[int, Document] = {}
        self.embedding_updates: list[tuple[int, str, int, str]] = []

    async def exists(self, document_id: int) -> bool:
        return document_id in self.documents

    async def create(
        self,
        document_id: int,
        title: str,
        body: str,
        metadata: dict[str, Any],
        status: DocumentStatus,
    ) -> Document:
        document = Document(
            id=None,
            document_id=document_id,
            title=title,
            body=body,
            metadata=metadata,
            status=status,
            is_deleted=False,
        )
        self.documents[document_id] = document
        return document

    async def get_by_document_id(self, document_id: int) -> Document | None:
        return self.documents.get(document_id)

    async def set_status(self, document_id: int, status: DocumentStatus) -> None:
        self.documents[document_id].status = status

    async def set_indexing_error(self, document_id: int, error: str | None) -> None:
        self.documents[document_id].indexing_error = error

    async def mark_deleted(self, document_id: int) -> None:
        document = self.documents[document_id]
        document.is_deleted = True
        document.status = DocumentStatus.DELETED

    async def get_active_by_ids(self, document_ids: list[int]) -> list[Document]:
        return [
            self.documents[document_id]
            for document_id in document_ids
            if document_id in self.documents and not self.documents[document_id].is_deleted
        ]

    async def update_embedding_info(
        self,
        document_id: int,
        model_name: str,
        dimension: int,
        version: str,
    ) -> None:
        document = self.documents[document_id]
        document.embedding_model_name = model_name
        document.embedding_dimension = dimension
        document.embedding_version = version
        self.embedding_updates.append((document_id, model_name, dimension, version))


class FakeChunkRepository:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.deleted_document_ids: list[int] = []

    async def save_many(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)

    async def count_by_document_id(self, document_id: int) -> int:
        return len([chunk for chunk in self.chunks if chunk.document_id == document_id and not chunk.is_deleted])

    async def get_by_document_id(self, document_id: int) -> list[Chunk]:
        return [chunk for chunk in self.chunks if chunk.document_id == document_id]

    async def mark_deleted_by_document_id(self, document_id: int) -> None:
        self.deleted_document_ids.append(document_id)
        for chunk in self.chunks:
            if chunk.document_id == document_id:
                chunk.is_deleted = True


class FakeVectorStore:
    def __init__(self, sources: list[Source] | None = None, fail_mark_deleted: bool = False) -> None:
        self.sources = sources or []
        self.ensure_collection_calls: list[int] = []
        self.upserts: list[tuple[list[Chunk], list[list[float]], dict[int, str]]] = []
        self.deleted_document_ids: list[int] = []
        self.fail_mark_deleted = fail_mark_deleted

    async def ensure_collection(self, vector_size: int) -> None:
        self.ensure_collection_calls.append(vector_size)

    async def upsert_chunks(
        self,
        chunks: list[Chunk],
        vectors: list[list[float]],
        titles: dict[int, str],
    ) -> None:
        self.upserts.append((chunks, vectors, titles))

    async def search(self, vector: list[float], top_k: int, filters: dict | None = None) -> list[Source]:
        return self.sources[:top_k]

    async def mark_deleted_by_document_id(self, document_id: int) -> None:
        if self.fail_mark_deleted:
            raise RuntimeError('qdrant is down')
        self.deleted_document_ids.append(document_id)


class FakeEmbeddingProvider:
    def __init__(self, dimension: int = 3, fail: bool = False) -> None:
        self.dimension = dimension
        self.fail = fail
        self.embedded_texts: list[str] = []

    async def embed_text(self, text: str) -> list[float]:
        if self.fail:
            raise RuntimeError('embedding failed')
        self.embedded_texts.append(text)
        return [1.0] * self.dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise RuntimeError('embedding failed')
        self.embedded_texts.extend(texts)
        return [[1.0] * self.dimension for _ in texts]

    def get_model_name(self) -> str:
        return 'fake-embedding'

    def get_dimension(self) -> int:
        return self.dimension

    def get_version(self) -> str:
        return 'test-v1'


class FakeJobQueue:
    def __init__(self) -> None:
        self.enqueued: list[int] = []

    async def enqueue_index_document(self, document_id: int) -> None:
        self.enqueued.append(document_id)


class FakeLLMProvider:
    def __init__(self, text: str = 'Сгенерированный ответ') -> None:
        self.text = text
        self.calls: list[tuple[str, str, float, int]] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self.calls.append((system_prompt, user_prompt, temperature, max_tokens))
        return LLMResponse(
            text=self.text,
            raw_response={'text': self.text},
            model_name='fake-llm',
            provider_name='fake',
        )


class FakeQueryLogRepository:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    async def save(self, **kwargs: Any) -> None:
        self.records.append(kwargs)

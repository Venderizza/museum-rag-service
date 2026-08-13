from abc import ABC, abstractmethod
from app.domain.entities.chunk import Chunk
from app.domain.entities.source import Source


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, vector_size: int) -> None: ...

    @abstractmethod
    async def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]], titles: dict[int, str]) -> None: ...

    @abstractmethod
    async def search(self, vector: list[float], top_k: int, filters: dict | None = None) -> list[Source]: ...

    @abstractmethod
    async def mark_deleted_by_document_id(self, document_id: int) -> None: ...

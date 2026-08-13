from abc import ABC, abstractmethod
from app.domain.entities.chunk import Chunk


class ChunkRepository(ABC):
    @abstractmethod
    async def save_many(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    async def count_by_document_id(self, document_id: int) -> int: ...

    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> list[Chunk]: ...

    @abstractmethod
    async def mark_deleted_by_document_id(self, document_id: int) -> None: ...

from abc import ABC, abstractmethod
from typing import Any
from app.domain.entities.document import Document
from app.domain.enums import DocumentStatus


class DocumentRepository(ABC):
    @abstractmethod
    async def exists(self, document_id: int) -> bool: ...

    @abstractmethod
    async def create(self, document_id: int, title: str, body: str, metadata: dict[str, Any], status: DocumentStatus) -> Document: ...

    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> Document | None: ...

    @abstractmethod
    async def set_status(self, document_id: int, status: DocumentStatus) -> None: ...

    @abstractmethod
    async def set_indexing_error(self, document_id: int, error: str | None) -> None: ...

    @abstractmethod
    async def mark_deleted(self, document_id: int) -> None: ...

    @abstractmethod
    async def get_active_by_ids(self, document_ids: list[int]) -> list[Document]: ...

    @abstractmethod
    async def update_embedding_info(self, document_id: int, model_name: str, dimension: int, version: str) -> None: ...

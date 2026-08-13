from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID
from app.domain.enums import DocumentStatus


@dataclass(slots=True)
class Document:
    id: UUID | None
    document_id: int
    title: str
    body: str
    metadata: dict[str, Any]
    status: DocumentStatus
    is_deleted: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    indexing_error: str | None = None
    embedding_model_name: str | None = None
    embedding_dimension: int | None = None
    embedding_version: str | None = None

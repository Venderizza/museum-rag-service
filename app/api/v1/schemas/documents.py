from typing import Any
from pydantic import BaseModel, Field
from app.domain.enums import DocumentStatus


class AddDocumentRequest(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentStatusResponse(BaseModel):
    document_id: int
    status: DocumentStatus
    chunks_count: int
    error: str | None = None


class DocumentMutationResponse(BaseModel):
    document_id: int
    status: DocumentStatus

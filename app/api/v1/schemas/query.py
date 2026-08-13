from pydantic import BaseModel, Field
from app.domain.enums import MessageRole, QueryStatus


class ChatMessageDTO(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1)


class QueryRequest(BaseModel):
    messages: list[ChatMessageDTO] = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)


class SourceDTO(BaseModel):
    document_id: int
    title: str
    score: float
    text: str


class QueryResponse(BaseModel):
    text: str
    id_list: list[int]
    sources: list[SourceDTO]
    confidence: float
    status: QueryStatus

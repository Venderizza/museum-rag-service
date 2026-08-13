from pydantic import BaseModel, Field
from app.api.v1.schemas.query import SourceDTO


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    results: list[SourceDTO]

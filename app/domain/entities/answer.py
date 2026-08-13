from dataclasses import dataclass
from app.domain.entities.source import Source
from app.domain.enums import QueryStatus


@dataclass(slots=True)
class QueryResult:
    text: str
    id_list: list[int]
    sources: list[Source]
    confidence: float
    status: QueryStatus

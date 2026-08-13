from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class Chunk:
    document_id: int
    chunk_index: int
    text: str
    embedding_model_name: str
    embedding_dimension: int
    embedding_version: str
    id: UUID = None  # type: ignore[assignment]
    char_start: int | None = None
    char_end: int | None = None
    token_count: int | None = None
    is_deleted: bool = False
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = uuid4()

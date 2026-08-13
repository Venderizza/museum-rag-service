from abc import ABC, abstractmethod
from app.domain.enums import QueryStatus


class QueryLogRepository(ABC):
    @abstractmethod
    async def save(
        self,
        *,
        messages_json: list[dict],
        normalized_query: str | None,
        answer_text: str | None,
        status: QueryStatus,
        confidence: float | None,
        used_document_ids: list[int],
        sources_json: list[dict],
        llm_provider: str | None,
        embedding_provider: str | None,
        retrieval_latency_ms: int | None,
        llm_latency_ms: int | None,
        total_latency_ms: int | None,
        prompt_text: str | None,
        raw_llm_response: str | None,
        error: str | None,
    ) -> None: ...

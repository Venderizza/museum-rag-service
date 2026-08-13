from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.enums import QueryStatus
from app.domain.ports.query_log_repository import QueryLogRepository
from app.infrastructure.db.models import QueryLogModel


class PostgresQueryLogRepository(QueryLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

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
    ) -> None:
        self.session.add(QueryLogModel(
            messages_json=messages_json,
            normalized_query=normalized_query,
            answer_text=answer_text,
            status=status.value,
            confidence=confidence,
            used_document_ids=used_document_ids,
            sources_json=sources_json,
            llm_provider=llm_provider,
            embedding_provider=embedding_provider,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            total_latency_ms=total_latency_ms,
            prompt_text=prompt_text,
            raw_llm_response=raw_llm_response,
            error=error,
            created_at=datetime.now(timezone.utc),
        ))
        await self.session.flush()

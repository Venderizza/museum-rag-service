import time
from app.application.services.confidence_service import ConfidenceService
from app.application.services.prompt_builder import PromptBuilder
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.entities.answer import QueryResult
from app.domain.entities.query import ChatMessage
from app.domain.enums import MessageRole, QueryStatus
from app.domain.errors import EmptyQueryError
from app.domain.ports.llm_provider import LLMProvider
from app.domain.ports.query_log_repository import QueryLogRepository


class QueryDocumentsUseCase:
    def __init__(
        self,
        search: SearchDocumentsUseCase,
        llm_provider: LLMProvider,
        query_logs: QueryLogRepository,
        prompt_builder: PromptBuilder,
        confidence_service: ConfidenceService,
        store_prompts: bool,
        store_raw_responses: bool,
    ):
        self.search = search
        self.llm_provider = llm_provider
        self.query_logs = query_logs
        self.prompt_builder = prompt_builder
        self.confidence_service = confidence_service
        self.store_prompts = store_prompts
        self.store_raw_responses = store_raw_responses

    async def execute(self, messages: list[ChatMessage], top_k: int) -> QueryResult:
        started = time.perf_counter()
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        if not user_messages or not user_messages[-1].content.strip():
            raise EmptyQueryError()
        query = user_messages[-1].content.strip()

        retrieval_started = time.perf_counter()
        sources = await self.search.execute(query, top_k)
        retrieval_ms = int((time.perf_counter() - retrieval_started) * 1000)
        confidence = self.confidence_service.calculate(sources)

        if not sources:
            result = QueryResult(
                text='Я не нашёл такой информации в базе музея.',
                id_list=[],
                sources=[],
                confidence=0.0,
                status=QueryStatus.NOT_FOUND,
            )
            await self._log(messages, query, result, retrieval_ms, None, int((time.perf_counter() - started) * 1000), None, None)
            return result

        if not self.confidence_service.has_enough_confidence(confidence):
            result = QueryResult(
                text='Я нашёл недостаточно информации в базе музея. Можете уточнить, о каком экспонате идёт речь?',
                id_list=list(dict.fromkeys(source.document_id for source in sources)),
                sources=sources,
                confidence=confidence,
                status=QueryStatus.NEEDS_CLARIFICATION,
            )
            await self._log(messages, query, result, retrieval_ms, None, int((time.perf_counter() - started) * 1000), None, None)
            return result

        system_prompt, user_prompt = self.prompt_builder.build(messages, sources)
        llm_started = time.perf_counter()
        llm_response = await self.llm_provider.generate(system_prompt, user_prompt)
        llm_ms = int((time.perf_counter() - llm_started) * 1000)

        result = QueryResult(
            text=llm_response.text,
            id_list=list(dict.fromkeys(source.document_id for source in sources)),
            sources=sources,
            confidence=confidence,
            status=QueryStatus.ANSWERED,
        )
        prompt_text = f'{system_prompt}\n\n{user_prompt}' if self.store_prompts else None
        raw = str(llm_response.raw_response) if self.store_raw_responses else None
        await self._log(messages, query, result, retrieval_ms, llm_ms, int((time.perf_counter() - started) * 1000), prompt_text, raw)
        return result

    async def _log(self, messages, query, result, retrieval_ms, llm_ms, total_ms, prompt_text, raw_response) -> None:
        await self.query_logs.save(
            messages_json=[{'role': m.role.value, 'content': m.content} for m in messages],
            normalized_query=query,
            answer_text=result.text,
            status=result.status,
            confidence=result.confidence,
            used_document_ids=result.id_list,
            sources_json=[{'document_id': source.document_id, 'title': source.title, 'score': source.score, 'text': source.text} for source in result.sources],
            llm_provider=None,
            embedding_provider=None,
            retrieval_latency_ms=retrieval_ms,
            llm_latency_ms=llm_ms,
            total_latency_ms=total_ms,
            prompt_text=prompt_text,
            raw_llm_response=raw_response,
            error=None,
        )

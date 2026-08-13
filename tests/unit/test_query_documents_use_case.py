import pytest

from app.application.services.confidence_service import ConfidenceService
from app.application.services.prompt_builder import PromptBuilder
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.entities.query import ChatMessage
from app.domain.entities.source import Source
from app.domain.enums import DocumentStatus, MessageRole, QueryStatus
from app.domain.errors import EmptyQueryError
from tests.support.fakes import (
    FakeDocumentRepository,
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeQueryLogRepository,
    FakeVectorStore,
)


async def _build_use_case(sources: list[Source], llm_text: str = 'Ответ'):
    documents = FakeDocumentRepository()
    for source in sources:
        await documents.create(source.document_id, source.title, source.text, {}, DocumentStatus.INDEXED)
    search = SearchDocumentsUseCase(documents, FakeVectorStore(sources), FakeEmbeddingProvider())
    llm = FakeLLMProvider(text=llm_text)
    logs = FakeQueryLogRepository()
    use_case = QueryDocumentsUseCase(
        search=search,
        llm_provider=llm,
        query_logs=logs,
        prompt_builder=PromptBuilder(),
        confidence_service=ConfidenceService(min_score=0.35, answer_threshold=0.45),
        store_prompts=True,
        store_raw_responses=True,
    )
    return use_case, llm, logs


@pytest.mark.asyncio
async def test_query_returns_answered_and_unique_document_ids():
    use_case, llm, logs = await _build_use_case(
        [
            Source(document_id=1, title='Экспонат', score=0.9, text='Фрагмент 1'),
            Source(document_id=1, title='Экспонат', score=0.8, text='Фрагмент 2'),
        ],
        llm_text='Ответ по базе',
    )

    result = await use_case.execute(
        [ChatMessage(role=MessageRole.USER, content='Расскажи про экспонат')],
        top_k=10,
    )

    assert result.status == QueryStatus.ANSWERED
    assert result.text == 'Ответ по базе'
    assert result.id_list == [1]
    assert len(llm.calls) == 1
    assert len(logs.records) == 1
    assert logs.records[0]['status'] == QueryStatus.ANSWERED
    assert logs.records[0]['prompt_text'] is not None


@pytest.mark.asyncio
async def test_query_returns_not_found_without_sources():
    use_case, llm, logs = await _build_use_case([])

    result = await use_case.execute(
        [ChatMessage(role=MessageRole.USER, content='нет такого')],
        top_k=10,
    )

    assert result.status == QueryStatus.NOT_FOUND
    assert result.id_list == []
    assert result.sources == []
    assert llm.calls == []
    assert logs.records[0]['status'] == QueryStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_query_returns_needs_clarification_for_low_confidence():
    use_case, llm, logs = await _build_use_case(
        [Source(document_id=1, title='Экспонат', score=0.2, text='Слабый фрагмент')]
    )

    result = await use_case.execute(
        [ChatMessage(role=MessageRole.USER, content='неясный вопрос')],
        top_k=10,
    )

    assert result.status == QueryStatus.NEEDS_CLARIFICATION
    assert result.id_list == [1]
    assert llm.calls == []
    assert logs.records[0]['status'] == QueryStatus.NEEDS_CLARIFICATION


@pytest.mark.asyncio
async def test_query_raises_empty_query_without_user_message():
    use_case, _, _ = await _build_use_case([])

    with pytest.raises(EmptyQueryError):
        await use_case.execute([ChatMessage(role=MessageRole.ASSISTANT, content='привет')], top_k=10)

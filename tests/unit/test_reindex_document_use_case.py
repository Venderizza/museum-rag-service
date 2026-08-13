import pytest

from app.application.use_cases.reindex_document import ReindexDocumentUseCase
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentDeletedError, DocumentNotFoundError
from tests.support.fakes import FakeChunkRepository, FakeDocumentRepository, FakeJobQueue, FakeVectorStore


@pytest.mark.asyncio
async def test_reindex_marks_old_data_deleted_and_enqueues_new_indexing():
    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    vector_store = FakeVectorStore()
    queue = FakeJobQueue()
    use_case = ReindexDocumentUseCase(documents, chunks, vector_store, queue)
    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.INDEXED)
    documents.documents[10].indexing_error = 'old error'

    status = await use_case.execute(10)

    assert status == DocumentStatus.QUEUED
    assert documents.documents[10].status == DocumentStatus.QUEUED
    assert documents.documents[10].indexing_error is None
    assert chunks.deleted_document_ids == [10]
    assert vector_store.deleted_document_ids == [10]
    assert queue.enqueued == [10]


@pytest.mark.asyncio
async def test_reindex_raises_for_missing_document():
    use_case = ReindexDocumentUseCase(
        FakeDocumentRepository(),
        FakeChunkRepository(),
        FakeVectorStore(),
        FakeJobQueue(),
    )

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(999)


@pytest.mark.asyncio
async def test_reindex_raises_for_deleted_document():
    documents = FakeDocumentRepository()
    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.DELETED)
    documents.documents[10].is_deleted = True
    use_case = ReindexDocumentUseCase(documents, FakeChunkRepository(), FakeVectorStore(), FakeJobQueue())

    with pytest.raises(DocumentDeletedError):
        await use_case.execute(10)

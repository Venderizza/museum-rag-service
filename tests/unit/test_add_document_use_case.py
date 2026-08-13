import pytest

from app.application.use_cases.add_document import AddDocumentUseCase
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentAlreadyExistsError
from tests.support.fakes import FakeDocumentRepository, FakeJobQueue


@pytest.mark.asyncio
async def test_add_document_creates_document_and_enqueues_indexing():
    documents = FakeDocumentRepository()
    queue = FakeJobQueue()
    use_case = AddDocumentUseCase(documents, queue)

    status = await use_case.execute(
        document_id=10,
        title='Экспонат',
        body='Описание',
        metadata={'source': 'test'},
    )

    assert status == DocumentStatus.QUEUED
    assert documents.documents[10].title == 'Экспонат'
    assert documents.documents[10].status == DocumentStatus.QUEUED
    assert queue.enqueued == [10]


@pytest.mark.asyncio
async def test_add_document_rejects_duplicate_document_id():
    documents = FakeDocumentRepository()
    queue = FakeJobQueue()
    use_case = AddDocumentUseCase(documents, queue)

    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.QUEUED)

    with pytest.raises(DocumentAlreadyExistsError):
        await use_case.execute(document_id=10, title='Дубль', body='Текст', metadata={})

    assert queue.enqueued == []

import pytest

from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentAlreadyDeletedError, DocumentNotFoundError
from tests.support.fakes import FakeChunkRepository, FakeDocumentRepository, FakeVectorStore


@pytest.mark.asyncio
async def test_delete_document_soft_deletes_document_chunks_and_vectors():
    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    vector_store = FakeVectorStore()
    use_case = DeleteDocumentUseCase(documents, chunks, vector_store)
    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.INDEXED)

    status = await use_case.execute(10)

    assert status == DocumentStatus.DELETED
    assert documents.documents[10].is_deleted is True
    assert chunks.deleted_document_ids == [10]
    assert vector_store.deleted_document_ids == [10]


@pytest.mark.asyncio
async def test_delete_document_keeps_postgres_deleted_even_if_vector_store_fails():
    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    vector_store = FakeVectorStore(fail_mark_deleted=True)
    use_case = DeleteDocumentUseCase(documents, chunks, vector_store)
    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.INDEXED)

    status = await use_case.execute(10)

    assert status == DocumentStatus.DELETED
    assert documents.documents[10].is_deleted is True
    assert chunks.deleted_document_ids == [10]


@pytest.mark.asyncio
async def test_delete_document_raises_for_missing_document():
    use_case = DeleteDocumentUseCase(FakeDocumentRepository(), FakeChunkRepository(), FakeVectorStore())

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(999)


@pytest.mark.asyncio
async def test_delete_document_raises_for_already_deleted_document():
    documents = FakeDocumentRepository()
    await documents.create(10, 'Экспонат', 'Описание', {}, DocumentStatus.DELETED)
    documents.documents[10].is_deleted = True
    use_case = DeleteDocumentUseCase(documents, FakeChunkRepository(), FakeVectorStore())

    with pytest.raises(DocumentAlreadyDeletedError):
        await use_case.execute(10)

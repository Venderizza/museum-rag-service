import pytest

from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.entities.source import Source
from app.domain.enums import DocumentStatus
from tests.support.fakes import FakeDocumentRepository, FakeEmbeddingProvider, FakeVectorStore


@pytest.mark.asyncio
async def test_search_returns_only_active_documents():
    documents = FakeDocumentRepository()
    await documents.create(1, 'Активный', 'Описание', {}, DocumentStatus.INDEXED)
    await documents.create(2, 'Удалённый', 'Описание', {}, DocumentStatus.DELETED)
    documents.documents[2].is_deleted = True
    vector_store = FakeVectorStore(
        sources=[
            Source(document_id=1, title='Активный', score=0.9, text='a'),
            Source(document_id=2, title='Удалённый', score=0.8, text='b'),
            Source(document_id=999, title='Нет в БД', score=0.7, text='c'),
        ]
    )
    embeddings = FakeEmbeddingProvider()
    use_case = SearchDocumentsUseCase(documents, vector_store, embeddings)

    results = await use_case.execute('экспонат', top_k=10)

    assert [source.document_id for source in results] == [1]
    assert embeddings.embedded_texts == ['экспонат']

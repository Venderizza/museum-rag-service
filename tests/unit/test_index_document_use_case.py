import pytest

from app.application.services.chunking_service import ChunkingService
from app.application.use_cases.index_document import IndexDocumentUseCase
from app.domain.enums import DocumentStatus
from app.domain.errors import DocumentNotFoundError
from tests.support.fakes import FakeChunkRepository, FakeDocumentRepository, FakeEmbeddingProvider, FakeVectorStore


@pytest.mark.asyncio
async def test_index_document_creates_chunks_vectors_and_marks_indexed():
    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    vector_store = FakeVectorStore()
    embeddings = FakeEmbeddingProvider(dimension=3)
    use_case = IndexDocumentUseCase(
        documents=documents,
        chunks=chunks,
        vector_store=vector_store,
        embedding_provider=embeddings,
        chunking_service=ChunkingService(chunk_size_tokens=100, chunk_overlap_tokens=10),
    )
    await documents.create(10, 'Шлем', 'Описание экспоната', {}, DocumentStatus.QUEUED)

    await use_case.execute(10)

    assert documents.documents[10].status == DocumentStatus.INDEXED
    assert documents.documents[10].embedding_model_name == 'fake-embedding'
    assert len(chunks.chunks) == 1
    assert vector_store.ensure_collection_calls == [3]
    assert len(vector_store.upserts) == 1
    assert vector_store.upserts[0][2] == {10: 'Шлем'}
    assert 'Название экспоната: Шлем' in embeddings.embedded_texts[0]


@pytest.mark.asyncio
async def test_index_document_ignores_deleted_document():
    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    vector_store = FakeVectorStore()
    use_case = IndexDocumentUseCase(
        documents=documents,
        chunks=chunks,
        vector_store=vector_store,
        embedding_provider=FakeEmbeddingProvider(),
        chunking_service=ChunkingService(chunk_size_tokens=100, chunk_overlap_tokens=10),
    )
    await documents.create(10, 'Шлем', 'Описание', {}, DocumentStatus.DELETED)
    documents.documents[10].is_deleted = True

    await use_case.execute(10)

    assert chunks.chunks == []
    assert vector_store.upserts == []


@pytest.mark.asyncio
async def test_index_document_raises_for_missing_document():
    use_case = IndexDocumentUseCase(
        documents=FakeDocumentRepository(),
        chunks=FakeChunkRepository(),
        vector_store=FakeVectorStore(),
        embedding_provider=FakeEmbeddingProvider(),
        chunking_service=ChunkingService(chunk_size_tokens=100, chunk_overlap_tokens=10),
    )

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(999)

from app.application.services.chunking_service import ChunkingService


def test_short_text_creates_one_chunk():
    service = ChunkingService(chunk_size_tokens=10, chunk_overlap_tokens=2)
    chunks = service.split(
        document_id=1,
        body='короткий текст экспоната',
        embedding_model_name='mock',
        embedding_dimension=3,
        embedding_version='v1',
    )
    assert len(chunks) == 1
    assert chunks[0].document_id == 1
    assert chunks[0].chunk_index == 0

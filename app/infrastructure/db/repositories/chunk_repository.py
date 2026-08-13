from datetime import datetime, timezone
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.chunk import Chunk
from app.domain.ports.chunk_repository import ChunkRepository
from app.infrastructure.db.models import ChunkModel


def to_domain(model: ChunkModel) -> Chunk:
    return Chunk(
        id=model.id,
        document_id=model.document_id,
        chunk_index=model.chunk_index,
        text=model.text,
        char_start=model.char_start,
        char_end=model.char_end,
        token_count=model.token_count,
        is_deleted=model.is_deleted,
        embedding_model_name=model.embedding_model_name,
        embedding_dimension=model.embedding_dimension,
        embedding_version=model.embedding_version,
        created_at=model.created_at,
    )


class PostgresChunkRepository(ChunkRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_many(self, chunks: list[Chunk]) -> None:
        now = datetime.now(timezone.utc)
        models = [
            ChunkModel(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                token_count=chunk.token_count,
                is_deleted=chunk.is_deleted,
                embedding_model_name=chunk.embedding_model_name,
                embedding_dimension=chunk.embedding_dimension,
                embedding_version=chunk.embedding_version,
                created_at=chunk.created_at or now,
            )
            for chunk in chunks
        ]
        self.session.add_all(models)
        await self.session.flush()

    async def count_by_document_id(self, document_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(ChunkModel).where(ChunkModel.document_id == document_id, ChunkModel.is_deleted.is_(False))
        )
        return int(result.scalar_one())

    async def get_by_document_id(self, document_id: int) -> list[Chunk]:
        result = await self.session.execute(
            select(ChunkModel).where(ChunkModel.document_id == document_id, ChunkModel.is_deleted.is_(False)).order_by(ChunkModel.chunk_index)
        )
        return [to_domain(model) for model in result.scalars().all()]

    async def mark_deleted_by_document_id(self, document_id: int) -> None:
        await self.session.execute(
            update(ChunkModel)
            .where(ChunkModel.document_id == document_id)
            .values(is_deleted=True)
        )

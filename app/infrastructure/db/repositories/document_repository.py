from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.document import Document
from app.domain.enums import DocumentStatus
from app.domain.ports.document_repository import DocumentRepository
from app.infrastructure.db.models import DocumentModel


def to_domain(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        document_id=model.document_id,
        title=model.title,
        body=model.body,
        metadata=model.doc_metadata,
        status=DocumentStatus(model.status),
        is_deleted=model.is_deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
        indexing_error=model.indexing_error,
        embedding_model_name=model.embedding_model_name,
        embedding_dimension=model.embedding_dimension,
        embedding_version=model.embedding_version,
    )


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, document_id: int) -> bool:
        result = await self.session.execute(select(DocumentModel.id).where(DocumentModel.document_id == document_id))
        return result.scalar_one_or_none() is not None

    async def create(self, document_id: int, title: str, body: str, metadata: dict[str, Any], status: DocumentStatus) -> Document:
        now = datetime.now(timezone.utc)
        model = DocumentModel(
            document_id=document_id,
            title=title,
            body=body,
            doc_metadata=metadata,
            status=status.value,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return to_domain(model)

    async def get_by_document_id(self, document_id: int) -> Document | None:
        result = await self.session.execute(select(DocumentModel).where(DocumentModel.document_id == document_id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def set_status(self, document_id: int, status: DocumentStatus) -> None:
        await self.session.execute(
            update(DocumentModel)
            .where(DocumentModel.document_id == document_id)
            .values(status=status.value, updated_at=datetime.now(timezone.utc))
        )

    async def set_indexing_error(self, document_id: int, error: str | None) -> None:
        await self.session.execute(
            update(DocumentModel)
            .where(DocumentModel.document_id == document_id)
            .values(indexing_error=error, updated_at=datetime.now(timezone.utc))
        )

    async def mark_deleted(self, document_id: int) -> None:
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(DocumentModel)
            .where(DocumentModel.document_id == document_id)
            .values(is_deleted=True, status=DocumentStatus.DELETED.value, deleted_at=now, updated_at=now)
        )

    async def get_active_by_ids(self, document_ids: list[int]) -> list[Document]:
        if not document_ids:
            return []
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.document_id.in_(document_ids), DocumentModel.is_deleted.is_(False))
        )
        return [to_domain(model) for model in result.scalars().all()]

    async def update_embedding_info(self, document_id: int, model_name: str, dimension: int, version: str) -> None:
        await self.session.execute(
            update(DocumentModel)
            .where(DocumentModel.document_id == document_id)
            .values(
                embedding_model_name=model_name,
                embedding_dimension=dimension,
                embedding_version=version,
                updated_at=datetime.now(timezone.utc),
            )
        )

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, Index, text as sql_text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(Base):
    __tablename__ = 'documents'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict] = mapped_column('metadata', JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    indexing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_dimension: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('ix_documents_status', 'status'),
        Index('ix_documents_is_deleted', 'is_deleted'),
    )


class ChunkModel(Base):
    __tablename__ = 'chunks'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding_model_name: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index('ix_chunks_document_id', 'document_id'),
        Index('ix_chunks_is_deleted', 'is_deleted'),
        Index(
            'ux_chunks_document_chunk_index_version_active',
            'document_id',
            'chunk_index',
            'embedding_version',
            unique=True,
            postgresql_where=sql_text('is_deleted = false'),
        ),
    )


class QueryLogModel(Base):
    __tablename__ = 'query_logs'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    messages_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    normalized_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    used_document_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    sources_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    llm_provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index('ix_query_logs_created_at', 'created_at'),
        Index('ix_query_logs_status', 'status'),
    )

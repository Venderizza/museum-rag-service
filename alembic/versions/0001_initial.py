"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-19
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('indexing_error', sa.Text(), nullable=True),
        sa.Column('embedding_model_name', sa.Text(), nullable=True),
        sa.Column('embedding_dimension', sa.Integer(), nullable=True),
        sa.Column('embedding_version', sa.Text(), nullable=True),
    )
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_is_deleted', 'documents', ['is_deleted'])

    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('char_start', sa.Integer(), nullable=True),
        sa.Column('char_end', sa.Integer(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('embedding_model_name', sa.Text(), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('embedding_version', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('document_id', 'chunk_index', 'embedding_version', name='ux_chunks_document_chunk_index_version'),
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_is_deleted', 'chunks', ['is_deleted'])

    op.create_table(
        'query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', sa.Text(), nullable=True),
        sa.Column('messages_json', postgresql.JSONB(), nullable=False),
        sa.Column('normalized_query', sa.Text(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('used_document_ids', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('sources_json', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('llm_provider', sa.Text(), nullable=True),
        sa.Column('embedding_provider', sa.Text(), nullable=True),
        sa.Column('retrieval_latency_ms', sa.Integer(), nullable=True),
        sa.Column('llm_latency_ms', sa.Integer(), nullable=True),
        sa.Column('total_latency_ms', sa.Integer(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=True),
        sa.Column('raw_llm_response', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_query_logs_created_at', 'query_logs', ['created_at'])
    op.create_index('ix_query_logs_status', 'query_logs', ['status'])


def downgrade() -> None:
    op.drop_table('query_logs')
    op.drop_table('chunks')
    op.drop_table('documents')

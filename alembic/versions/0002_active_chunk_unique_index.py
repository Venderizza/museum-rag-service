"""replace chunk unique constraint with active-only partial index

Revision ID: 0002_active_chunk_unique_index
Revises: 0001_initial
Create Date: 2026-05-19
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = '0002_active_chunk_unique_index'
down_revision: str | None = '0001_initial'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('ux_chunks_document_chunk_index_version', 'chunks', type_='unique')
    op.create_index(
        'ux_chunks_document_chunk_index_version_active',
        'chunks',
        ['document_id', 'chunk_index', 'embedding_version'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
    )


def downgrade() -> None:
    op.drop_index('ux_chunks_document_chunk_index_version_active', table_name='chunks')
    op.create_unique_constraint(
        'ux_chunks_document_chunk_index_version',
        'chunks',
        ['document_id', 'chunk_index', 'embedding_version'],
    )

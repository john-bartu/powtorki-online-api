"""page add document_json

Adds pages.document_json (nullable JSON) -- the ProseMirror/TipTap JSON form of
DocumentPage.document (legacy HTML), produced by app.tools.document_conversion.
Populated for existing rows by a one-off run of app.tools.import_documents;
`document` itself is left untouched as a fallback, not migrated away.

Revision ID: 8e50444ad137
Revises: bd63705a02af
Create Date: 2026-08-16 13:58:06.846993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e50444ad137'
down_revision: Union[str, Sequence[str], None] = 'bd63705a02af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pages', sa.Column('document_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('pages', 'document_json')

"""test session page: add given answer

Adds map_test_session_page.id_answer (nullable) -- which answer choice was actually
submitted for a graded quiz page, so a past session can be reviewed answer-by-answer.
Flashcard grades (Character/Date/Dictionary/QA) have no answer choice and leave this
NULL.

Revision ID: bd63705a02af
Revises: 063786a01201
Create Date: 2026-08-15 20:22:46.758805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd63705a02af'
down_revision: Union[str, Sequence[str], None] = '063786a01201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('map_test_session_page',
                  sa.Column('id_answer', sa.Integer(), sa.ForeignKey('answers.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('map_test_session_page', 'id_answer')

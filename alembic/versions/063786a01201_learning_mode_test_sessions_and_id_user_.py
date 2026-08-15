"""learning mode: test sessions and id_user not null

Backfills map_user_quiz_answer.id_user (100% NULL today - the write path
never set it, see app.services.quiz_service.QuizService.answer) to user id 1,
the same placeholder id_user already used for every historical
map_user_activity row (see app.services.page_service/quiz_service). Both
columns then become NOT NULL, matching the app now always sourcing id_user
from an authenticated caller (app.auth.dependencies.get_current_user /
get_current_user_optional) instead of leaving it unset or hardcoded.

Also adds the two new tables backing Learning Mode: `test_sessions` and
`map_test_session_page` (see app.database.models.test_session).

Revision ID: 063786a01201
Revises: 19ad27e654b3
Create Date: 2026-08-15 18:23:00.406260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '063786a01201'
down_revision: Union[str, Sequence[str], None] = '19ad27e654b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLACEHOLDER_USER_ID = 1


def upgrade() -> None:
    op.execute(f"UPDATE map_user_quiz_answer SET id_user = {PLACEHOLDER_USER_ID} WHERE id_user IS NULL")
    op.alter_column('map_user_quiz_answer', 'id_user', existing_type=sa.Integer(), nullable=False)
    op.alter_column('map_user_activity', 'id_user', existing_type=sa.Integer(), nullable=False)

    op.create_table(
        'test_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('id_user', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('id_taxonomy', sa.Integer(), sa.ForeignKey('taxonomies.id'), nullable=False),
        sa.Column('included_types', sa.JSON(), nullable=False),
        sa.Column('status', sa.VARCHAR(20), nullable=False, server_default='in_progress'),
        sa.Column('time_creation', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('time_completed', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'map_test_session_page',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('id_test_session', sa.Integer(), sa.ForeignKey('test_sessions.id'), nullable=False),
        sa.Column('id_page', sa.Integer(), sa.ForeignKey('pages.id'), nullable=False),
        sa.Column('is_known', sa.Boolean(), nullable=False),
        sa.Column('time_answered', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('id_test_session', 'id_page', name='uq_test_session_page'),
    )
    op.create_index('ix_map_test_session_page_id_page', 'map_test_session_page', ['id_page'])


def downgrade() -> None:
    op.drop_index('ix_map_test_session_page_id_page', table_name='map_test_session_page')
    op.drop_table('map_test_session_page')
    op.drop_table('test_sessions')

    op.alter_column('map_user_activity', 'id_user', existing_type=sa.Integer(), nullable=True)
    op.alter_column('map_user_quiz_answer', 'id_user', existing_type=sa.Integer(), nullable=True)

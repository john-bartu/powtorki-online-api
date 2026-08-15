"""baseline

This revision is deliberately a no-op. The schema was hand-managed via
DataGrip/PyCharm before Alembic existed, so `alembic revision --autogenerate`
against the live DB produces a large diff against the SQLAlchemy models that
has nothing to do with this feature (dropped legacy tables like
`product_keys`/`map_user_product_key`, renamed/missing columns, differing
index names, etc.) — years of drift, not intentional change.

Rather than encode that drift as executable migration operations (which would
risk dropping/altering things nobody asked to touch), this revision exists
purely as the pinned starting point: run `alembic stamp 19ad27e654b3` against
each existing environment (dev/prod) to record "this DB is already at this
revision" without executing any DDL. Every migration after this one is a real,
intentional schema change written by hand.

Revision ID: 19ad27e654b3
Revises:
Create Date: 2026-08-15 18:21:25.038204

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '19ad27e654b3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

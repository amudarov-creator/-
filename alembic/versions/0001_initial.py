"""Initial provenance-first CS2 analytics schema.

Revision ID: 0001_initial
"""
from alembic import op
from app.database.base import Base
from app.database import models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())

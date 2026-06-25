"""add close and change columns to quotes

Revision ID: 002
Revises: 001
Create Date: 2026-06-25
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS close NUMERIC")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS change NUMERIC")


def downgrade() -> None:
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS close")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS change")

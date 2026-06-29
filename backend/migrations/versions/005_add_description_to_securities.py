"""add description column to securities

Revision ID: 005
Revises: 004
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE securities ADD COLUMN IF NOT EXISTS description TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE securities DROP COLUMN IF EXISTS description")

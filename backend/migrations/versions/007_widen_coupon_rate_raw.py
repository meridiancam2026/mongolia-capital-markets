"""widen coupon_rate_raw column to VARCHAR(50)

Revision ID: 007
Revises: 006
Create Date: 2026-06-29
"""
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE otc_bond_registry ALTER COLUMN coupon_rate_raw TYPE VARCHAR(50)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE otc_bond_registry ALTER COLUMN coupon_rate_raw TYPE VARCHAR(20)"
    )

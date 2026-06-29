"""change variable-length otc_bond_registry columns to TEXT

Revision ID: 008
Revises: 007
Create Date: 2026-06-29
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in ("coupon_rate_raw", "status", "sector", "underwriter", "currency"):
        op.execute(
            f"ALTER TABLE otc_bond_registry ALTER COLUMN {col} TYPE TEXT"
        )


def downgrade() -> None:
    pass

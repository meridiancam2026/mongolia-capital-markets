"""add cbonds_id to otc_trades and create bond_price_history table

Revision ID: 009
Revises: 008
Create Date: 2026-06-30
"""
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE otc_trades ADD COLUMN IF NOT EXISTS cbonds_id INTEGER"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS bond_price_history (
            id          BIGSERIAL PRIMARY KEY,
            bond_name   TEXT NOT NULL,
            cbonds_id   INTEGER,
            trade_date  DATE NOT NULL,
            price       NUMERIC,
            yield       NUMERIC,
            currency    VARCHAR(10),
            CONSTRAINT uq_bond_price_history UNIQUE (bond_name, trade_date)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_bond_history_name_date "
        "ON bond_price_history (bond_name, trade_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bond_price_history")
    op.execute("ALTER TABLE otc_trades DROP COLUMN IF EXISTS cbonds_id")

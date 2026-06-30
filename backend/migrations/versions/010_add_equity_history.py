"""add equity_price_history table for daily close snapshots

Revision ID: 010
Revises: 009
Create Date: 2026-06-30
"""
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS equity_price_history (
            id          BIGSERIAL PRIMARY KEY,
            ticker      VARCHAR(10) NOT NULL REFERENCES securities(ticker),
            trade_date  DATE NOT NULL,
            open        NUMERIC,
            high        NUMERIC,
            low         NUMERIC,
            close       NUMERIC,
            change      NUMERIC,
            change_pct  NUMERIC,
            volume      BIGINT,
            value       NUMERIC,
            CONSTRAINT uq_equity_history UNIQUE (ticker, trade_date)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_equity_history_ticker_date "
        "ON equity_price_history (ticker, trade_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS equity_price_history")

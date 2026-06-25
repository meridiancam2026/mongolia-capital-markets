"""create securities and quotes tables

Revision ID: 001
Revises:
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS securities (
            ticker       VARCHAR(10) PRIMARY KEY,
            name         TEXT,
            isin         VARCHAR(12),
            sector       VARCHAR(50),
            listing_date DATE,
            status       VARCHAR(10) DEFAULT 'active'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id          BIGSERIAL PRIMARY KEY,
            ticker      VARCHAR(10) NOT NULL REFERENCES securities(ticker),
            trade_time  TIMESTAMPTZ NOT NULL,
            open        NUMERIC,
            high        NUMERIC,
            low         NUMERIC,
            last        NUMERIC,
            prev_close  NUMERIC,
            change_pct  NUMERIC,
            volume      BIGINT,
            value       NUMERIC,
            bid_price   NUMERIC,
            bid_qty     BIGINT,
            ask_price   NUMERIC,
            ask_qty     BIGINT,
            CONSTRAINT uq_quotes_ticker_time UNIQUE (ticker, trade_time)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_quotes_ticker ON quotes (ticker)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotes_trade_time ON quotes (trade_time DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quotes")
    op.execute("DROP TABLE IF EXISTS securities")

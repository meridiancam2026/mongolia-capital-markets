"""create otc_trades, macro, and regulatory_stats tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-25
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS otc_trades (
            id          BIGSERIAL PRIMARY KEY,
            bond_name   TEXT NOT NULL,
            price       NUMERIC,
            yield       NUMERIC,
            volume      BIGINT,
            value       NUMERIC,
            trade_date  DATE NOT NULL,
            market_type VARCHAR(20),
            CONSTRAINT uq_otc_trades UNIQUE (bond_name, trade_date)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otc_trades_date ON otc_trades (trade_date DESC)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS macro (
            id             SERIAL PRIMARY KEY,
            indicator      VARCHAR(50) NOT NULL,
            value          NUMERIC,
            reference_date DATE NOT NULL,
            source         VARCHAR(50),
            CONSTRAINT uq_macro UNIQUE (indicator, reference_date)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_macro_indicator ON macro (indicator, reference_date DESC)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS regulatory_stats (
            id             SERIAL PRIMARY KEY,
            indicator      VARCHAR(100) NOT NULL,
            value          NUMERIC,
            unit           VARCHAR(20),
            reference_year INTEGER NOT NULL,
            source         VARCHAR(100),
            notes          TEXT,
            CONSTRAINT uq_regulatory_stats UNIQUE (indicator, reference_year)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS regulatory_stats")
    op.execute("DROP TABLE IF EXISTS macro")
    op.execute("DROP TABLE IF EXISTS otc_trades")

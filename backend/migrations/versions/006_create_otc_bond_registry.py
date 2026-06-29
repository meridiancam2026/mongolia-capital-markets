"""create otc_bond_registry table

Revision ID: 006
Revises: 005
Create Date: 2026-06-29
"""
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS otc_bond_registry (
            id              SERIAL PRIMARY KEY,
            bond_name       VARCHAR(200) NOT NULL,
            board_category  VARCHAR(5),
            sector          VARCHAR(100),
            issue_date      DATE,
            currency        VARCHAR(10),
            maturity_months INTEGER,
            coupon_rate_raw VARCHAR(20),
            coupon_rate     NUMERIC,
            underwriter     VARCHAR(200),
            status          VARCHAR(30),
            scraped_date    DATE NOT NULL,
            CONSTRAINT uq_otc_bond_registry UNIQUE (bond_name)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otc_registry_board ON otc_bond_registry (board_category)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otc_registry_sector ON otc_bond_registry (sector)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS otc_bond_registry")

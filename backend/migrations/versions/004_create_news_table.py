"""create news table

Revision ID: 004
Revises: 003
Create Date: 2026-06-25
"""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id           SERIAL PRIMARY KEY,
            title        TEXT NOT NULL,
            summary      TEXT,
            source_url   TEXT UNIQUE,
            published_at TIMESTAMPTZ
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_published_at ON news (published_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS news")

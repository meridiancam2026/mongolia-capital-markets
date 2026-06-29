import os
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_project_root = Path(__file__).resolve().parents[1]
load_dotenv(_project_root / ".env")

# Fall back to a placeholder so the module is importable during tests
# (get_db is overridden in tests before any real connection is made)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost/placeholder",
)

# Normalize scheme — Render/Heroku provide postgres:// or bare postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

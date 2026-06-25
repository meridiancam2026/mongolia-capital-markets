"""Shared fixtures for FastAPI route tests."""
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.database import get_db
from backend.main import app


@pytest.fixture
def mock_db():
    # Explicitly set return_value to a plain MagicMock so that result.scalars()
    # and result.mappings() are regular (non-async) calls — Python 3.14's AsyncMock
    # otherwise makes its return_value an AsyncMock too, causing AttributeError.
    result = MagicMock()
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=None)
    return session


@pytest_asyncio.fixture
async def async_client(mock_db):
    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()

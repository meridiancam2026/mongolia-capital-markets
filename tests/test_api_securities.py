"""Tests for GET /api/securities."""
import pytest
from backend.models import Security


def _make_security(ticker: str, name: str = None, sector: str = None) -> Security:
    s = Security()
    s.ticker = ticker
    s.name = name
    s.isin = None
    s.sector = sector
    s.listing_date = None
    s.status = "active"
    return s


@pytest.mark.asyncio
async def test_securities_returns_200(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    resp = await async_client.get("/api/securities")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_securities_returns_list(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_security("APU", "APU JSC"),
        _make_security("TDB", "Trade and Development Bank"),
    ]
    resp = await async_client.get("/api/securities")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_securities_ticker_field(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_security("XAC", "XacBank")
    ]
    resp = await async_client.get("/api/securities")
    assert resp.json()[0]["ticker"] == "XAC"


@pytest.mark.asyncio
async def test_securities_empty(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    resp = await async_client.get("/api/securities")
    assert resp.json() == []

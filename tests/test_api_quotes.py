"""Tests for GET /api/quotes and GET /api/quotes/{ticker}."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from backend.models import Quote, Security


def _make_quote(ticker: str = "APU") -> dict:
    return {
        "id": 1,
        "ticker": ticker,
        "trade_time": datetime(2026, 6, 25, 10, 0, tzinfo=timezone.utc),
        "open": Decimal("1500.00"),
        "high": Decimal("1520.00"),
        "low": Decimal("1490.00"),
        "last": Decimal("1510.00"),
        "prev_close": Decimal("1495.00"),
        "close": Decimal("1510.00"),
        "change": Decimal("15.00"),
        "change_pct": Decimal("1.00"),
        "volume": 10000,
        "value": Decimal("15100000.00"),
        "bid_price": Decimal("1508.00"),
        "bid_qty": 500,
        "ask_price": Decimal("1512.00"),
        "ask_qty": 300,
    }


def _make_quote_orm(ticker: str = "APU") -> Quote:
    q = Quote()
    for k, v in _make_quote(ticker).items():
        setattr(q, k, v)
    return q


@pytest.mark.asyncio
async def test_quotes_returns_200(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    resp = await async_client.get("/api/quotes")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_quotes_returns_list(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        _make_quote("APU"),
        _make_quote("XAC"),
    ]
    resp = await async_client.get("/api/quotes")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_quotes_decimal_as_string(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = [_make_quote()]
    resp = await async_client.get("/api/quotes")
    q = resp.json()[0]
    assert isinstance(q["open"], str)
    assert q["open"] == "1500.00"


@pytest.mark.asyncio
async def test_quotes_value_precision(async_client, mock_db):
    row = _make_quote()
    row["value"] = Decimal("141700000000")
    mock_db.execute.return_value.mappings.return_value.all.return_value = [row]
    resp = await async_client.get("/api/quotes")
    assert resp.json()[0]["value"] == "141700000000"


@pytest.mark.asyncio
async def test_quotes_ticker_404(async_client, mock_db):
    mock_db.get.return_value = None
    resp = await async_client.get("/api/quotes/NOTEXIST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_quotes_ticker_returns_list(async_client, mock_db):
    mock_db.get.return_value = Security()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_quote_orm("APU")
    ]
    resp = await async_client.get("/api/quotes/APU")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

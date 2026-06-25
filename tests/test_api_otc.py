"""Tests for GET /api/otc."""
from datetime import date
from decimal import Decimal

import pytest
from backend.models import OtcTrade


def _make_otc(bond_name: str = "Neo power bond 1") -> OtcTrade:
    t = OtcTrade()
    t.id = 1
    t.bond_name = bond_name
    t.trade_date = date(2026, 6, 25)
    t.price = None
    t.yield_ = None
    t.volume = None
    t.value = Decimal("25000000000")
    t.market_type = None
    return t


@pytest.mark.asyncio
async def test_otc_returns_200(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    resp = await async_client.get("/api/otc")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_otc_returns_list(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_otc("Neo power bond 1"),
        _make_otc("Edelmont bond 1"),
    ]
    resp = await async_client.get("/api/otc")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_otc_value_is_string(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [_make_otc()]
    resp = await async_client.get("/api/otc")
    assert isinstance(resp.json()[0]["value"], str)
    assert resp.json()[0]["value"] == "25000000000"


@pytest.mark.asyncio
async def test_otc_yield_null(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [_make_otc()]
    resp = await async_client.get("/api/otc")
    assert resp.json()[0]["yield"] is None

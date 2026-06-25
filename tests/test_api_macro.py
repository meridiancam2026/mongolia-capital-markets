"""Tests for GET /api/macro and GET /api/macro/fx."""
from datetime import date
from decimal import Decimal

import pytest


def _make_row(indicator: str, value: Decimal) -> dict:
    return {
        "id": 1,
        "indicator": indicator,
        "value": value,
        "reference_date": date(2026, 6, 25),
        "source": "open.er-api.com",
    }


@pytest.mark.asyncio
async def test_macro_returns_200(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    resp = await async_client.get("/api/macro")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_macro_returns_list(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        _make_row("FX_USD_MNT", Decimal("3586.26")),
        _make_row("FX_EUR_MNT", Decimal("4071.57")),
    ]
    resp = await async_client.get("/api/macro")
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_macro_value_is_string(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        _make_row("FX_USD_MNT", Decimal("3586.26"))
    ]
    resp = await async_client.get("/api/macro")
    assert isinstance(resp.json()[0]["value"], str)
    assert resp.json()[0]["value"] == "3586.26"


@pytest.mark.asyncio
async def test_macro_fx_returns_200(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    resp = await async_client.get("/api/macro/fx")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_macro_fx_only_fx_indicators(async_client, mock_db):
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        _make_row("FX_USD_MNT", Decimal("3586.26")),
        _make_row("FX_CNY_MNT", Decimal("526.02")),
    ]
    resp = await async_client.get("/api/macro/fx")
    data = resp.json()
    assert all(r["indicator"].startswith("FX_") for r in data)

"""Tests for GET /api/regulatory."""
from decimal import Decimal

import pytest
from backend.models import RegulatoryStats


def _make_stat(indicator: str, value: Decimal, year: int = 2024) -> RegulatoryStats:
    s = RegulatoryStats()
    s.id = 1
    s.indicator = indicator
    s.value = value
    s.unit = "MNT"
    s.reference_year = year
    s.source = "FRC"
    s.notes = None
    return s


@pytest.mark.asyncio
async def test_regulatory_returns_200(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    resp = await async_client.get("/api/regulatory")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_regulatory_returns_list(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_stat("policy_rate", Decimal("12.00")),
        _make_stat("listed_companies", Decimal("44")),
    ]
    resp = await async_client.get("/api/regulatory")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_regulatory_value_is_string(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_stat("policy_rate", Decimal("12.00"))
    ]
    resp = await async_client.get("/api/regulatory")
    assert isinstance(resp.json()[0]["value"], str)
    assert resp.json()[0]["value"] == "12.00"


@pytest.mark.asyncio
async def test_regulatory_has_unit_and_notes(async_client, mock_db):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        _make_stat("policy_rate", Decimal("12.00"))
    ]
    resp = await async_client.get("/api/regulatory")
    item = resp.json()[0]
    assert "unit" in item
    assert "notes" in item

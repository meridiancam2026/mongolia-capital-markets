"""Unit tests for ingest_macro.py — no live HTTP or DB calls."""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ingest_macro import parse_fx_rates, parse_policy_rate, upsert_macro, scrape_fx_openexchange


# ── HTML fixtures ──────────────────────────────────────────────────────────────

FX_HTML = """
<html><body>
<table>
  <thead><tr><th>Currency</th><th>Units</th><th>Rate</th></tr></thead>
  <tbody>
    <tr><td>USD</td><td>1</td><td>3,450.00</td></tr>
    <tr><td>EUR</td><td>1</td><td>3,720.50</td></tr>
    <tr><td>CNY</td><td>1</td><td>474.80</td></tr>
    <tr><td>RUB</td><td>100</td><td>3,810.00</td></tr>
    <tr><td>GBP</td><td>1</td><td>4,350.00</td></tr>
  </tbody>
</table>
</body></html>
"""

FX_HTML_EMPTY = "<html><body><p>No data available</p></body></html>"

POLICY_HTML = """
<html><body>
<h1>Monetary Policy Rate</h1>
<div class="rate-card">
  <span class="rate-value">12.00</span>
  <span class="rate-unit">%</span>
</div>
</body></html>
"""

POLICY_HTML_NO_RATE = "<html><body><p>Page under maintenance</p></body></html>"


# ── parse_fx_rates ─────────────────────────────────────────────────────────────

def test_parse_fx_rates_returns_list():
    rows = parse_fx_rates(FX_HTML)
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_parse_fx_rates_usd_present():
    rows = parse_fx_rates(FX_HTML)
    indicators = [r["indicator"] for r in rows]
    assert "FX_USD_MNT" in indicators


def test_parse_fx_rates_usd_value():
    rows = parse_fx_rates(FX_HTML)
    usd = next(r for r in rows if r["indicator"] == "FX_USD_MNT")
    assert usd["value"] == Decimal("3450.00")


def test_parse_fx_rates_eur_present():
    rows = parse_fx_rates(FX_HTML)
    indicators = [r["indicator"] for r in rows]
    assert "FX_EUR_MNT" in indicators


def test_parse_fx_rates_source_is_bom():
    rows = parse_fx_rates(FX_HTML)
    assert all(r["source"] == "BOM" for r in rows)


def test_parse_fx_rates_has_reference_date():
    rows = parse_fx_rates(FX_HTML)
    for r in rows:
        assert isinstance(r["reference_date"], date)


def test_parse_fx_rates_empty_page_returns_empty():
    rows = parse_fx_rates(FX_HTML_EMPTY)
    assert rows == []


# ── parse_policy_rate ──────────────────────────────────────────────────────────

def test_parse_policy_rate_returns_dict():
    result = parse_policy_rate(POLICY_HTML)
    assert result is not None
    assert result["indicator"] == "POLICY_RATE"


def test_parse_policy_rate_value():
    result = parse_policy_rate(POLICY_HTML)
    assert result is not None
    assert result["value"] == Decimal("12.00")


def test_parse_policy_rate_source_is_bom():
    result = parse_policy_rate(POLICY_HTML)
    assert result is not None
    assert result["source"] == "BOM"


def test_parse_policy_rate_no_rate_returns_none():
    result = parse_policy_rate(POLICY_HTML_NO_RATE)
    assert result is None


# ── scrape_fx_openexchange (mocked HTTP) ──────────────────────────────────────

OPENEXCHANGE_RESPONSE = {
    "result": "success",
    "rates": {"MNT": 3586.26, "EUR": 0.9107, "CNY": 7.249, "GBP": 0.7801},
}


def test_scrape_fx_openexchange_returns_usd_mnt():
    mock_resp = MagicMock()
    mock_resp.json.return_value = OPENEXCHANGE_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    with patch("ingest_macro.requests.get", return_value=mock_resp):
        rows = scrape_fx_openexchange()
    indicators = {r["indicator"] for r in rows}
    assert "FX_USD_MNT" in indicators


def test_scrape_fx_openexchange_usd_value():
    mock_resp = MagicMock()
    mock_resp.json.return_value = OPENEXCHANGE_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    with patch("ingest_macro.requests.get", return_value=mock_resp):
        rows = scrape_fx_openexchange()
    usd = next(r for r in rows if r["indicator"] == "FX_USD_MNT")
    assert usd["value"] == Decimal("3586.26")


def test_scrape_fx_openexchange_includes_eur():
    mock_resp = MagicMock()
    mock_resp.json.return_value = OPENEXCHANGE_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    with patch("ingest_macro.requests.get", return_value=mock_resp):
        rows = scrape_fx_openexchange()
    indicators = {r["indicator"] for r in rows}
    assert "FX_EUR_MNT" in indicators


def test_scrape_fx_openexchange_error_returns_empty():
    import requests as req
    with patch("ingest_macro.requests.get", side_effect=req.RequestException("timeout")):
        rows = scrape_fx_openexchange()
    assert rows == []


# ── upsert_macro (mocked DB) ───────────────────────────────────────────────────

def test_upsert_empty_rows_returns_zero():
    assert upsert_macro([]) == 0


def test_upsert_calls_execute_per_row():
    rows = parse_fx_rates(FX_HTML)
    assert len(rows) >= 2

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("ingest_macro.get_db_conn", return_value=mock_conn):
        result = upsert_macro(rows)

    assert result == len(rows)
    assert mock_cursor.execute.call_count == len(rows)

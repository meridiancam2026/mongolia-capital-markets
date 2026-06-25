"""Unit tests for ingest_otc.py — no live site or DB calls."""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ingest_otc import (
    parse_row, _to_decimal, _to_int, _to_date, _parse_tbm_value,
    parse_market_summary, insert_otc_trades,
)
from bs4 import BeautifulSoup


# ── _to_decimal ────────────────────────────────────────────────────────────────

def test_to_decimal_plain():
    assert _to_decimal("12.5") == Decimal("12.5")

def test_to_decimal_percent():
    assert _to_decimal("8.75%") == Decimal("8.75")

def test_to_decimal_with_commas():
    assert _to_decimal("1,250,000") == Decimal("1250000")

def test_to_decimal_empty():
    assert _to_decimal("") is None

def test_to_decimal_dash():
    assert _to_decimal("-") is None


# ── _to_int ────────────────────────────────────────────────────────────────────

def test_to_int_plain():
    assert _to_int("5000") == 5000

def test_to_int_commas():
    assert _to_int("1,000,000") == 1_000_000

def test_to_int_empty():
    assert _to_int("") is None


# ── _to_date ───────────────────────────────────────────────────────────────────

def test_to_date_iso():
    assert _to_date("2026-06-25") == date(2026, 6, 25)

def test_to_date_dots():
    assert _to_date("2026.06.25") == date(2026, 6, 25)

def test_to_date_slash():
    assert _to_date("25/06/2026") == date(2026, 6, 25)

def test_to_date_empty():
    assert _to_date("") is None

def test_to_date_dash():
    assert _to_date("-") is None


# ── _parse_tbm_value ───────────────────────────────────────────────────────────

def test_parse_tbm_25():
    assert _parse_tbm_value("₮25.0ТБ") == Decimal("25000000000")

def test_parse_tbm_141():
    assert _parse_tbm_value("₮141.7ТБ") == Decimal("141700000000")

def test_parse_tbm_empty():
    assert _parse_tbm_value("") is None


# ── parse_row ──────────────────────────────────────────────────────────────────
# MASD bond table cells: [rank, bond_name, value_tbm]

def test_parse_row_valid():
    row = parse_row(["1", "Neo power bond 1", "₮25.0ТБ"])
    assert row is not None
    assert row["bond_name"] == "Neo power bond 1"
    assert row["value"] == Decimal("25000000000")
    assert isinstance(row["trade_date"], date)
    assert row["price"] is None
    assert row["yield"] is None


def test_parse_row_empty_bond_name():
    assert parse_row(["1", "", "₮25.0ТБ"]) is None


def test_parse_row_mongolian_header_skipped():
    assert parse_row(["#", "НЭРШИЛ", "ҮНЭ"]) is None


def test_parse_row_too_short():
    assert parse_row(["1", "Neo power bond 1"]) is None


def test_parse_row_second_entry():
    row = parse_row(["2", "Edelmont bond 1", "₮20.0ТБ"])
    assert row is not None
    assert row["bond_name"] == "Edelmont bond 1"
    assert row["value"] == Decimal("20000000000")


# ── parse_market_summary ───────────────────────────────────────────────────────

SUMMARY_HTML = """
<html><body>
<div class="grid">
  <div>Хоёрдогч зах зээлөнөөдөр₮12.5 тэрбум</div>
  <div>Анхдагч зах зээлөнөөдөр₮45.4 тэрбум</div>
  <div>Нийт ОТС бондын үлдэгдэл₮4.05 тэрбум</div>
</div>
</body></html>
"""

def test_parse_market_summary_secondary():
    soup = BeautifulSoup(SUMMARY_HTML, "html.parser")
    rows = parse_market_summary(soup)
    indicators = {r["indicator"]: r["value"] for r in rows}
    assert "MASD_SECONDARY_MARKET_MNT" in indicators
    assert indicators["MASD_SECONDARY_MARKET_MNT"] == Decimal("12500000000")


def test_parse_market_summary_primary():
    soup = BeautifulSoup(SUMMARY_HTML, "html.parser")
    rows = parse_market_summary(soup)
    indicators = {r["indicator"]: r["value"] for r in rows}
    assert "MASD_PRIMARY_MARKET_MNT" in indicators
    assert indicators["MASD_PRIMARY_MARKET_MNT"] == Decimal("45400000000")


def test_parse_market_summary_source_is_masd():
    soup = BeautifulSoup(SUMMARY_HTML, "html.parser")
    rows = parse_market_summary(soup)
    assert all(r["source"] == "MASD" for r in rows)


def test_parse_market_summary_empty_html():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    assert parse_market_summary(soup) == []


# ── insert_otc_trades (mocked DB) ─────────────────────────────────────────────

def test_insert_empty_rows_returns_zero():
    assert insert_otc_trades([]) == 0


def test_insert_calls_execute_per_row():
    rows = [
        parse_row(["1", "Neo power bond 1", "₮25.0ТБ"]),
        parse_row(["2", "Edelmont bond 1", "₮20.0ТБ"]),
    ]

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("ingest_otc.get_db_conn", return_value=mock_conn):
        result = insert_otc_trades(rows)

    assert result == 2
    assert mock_cursor.execute.call_count == 2

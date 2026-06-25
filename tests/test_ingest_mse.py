"""Unit tests for ingest_mse.py — no live site or DB calls."""
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ingest_mse import parse_row, _to_decimal, _to_int, upsert_quotes


# ── _to_decimal ────────────────────────────────────────────────────────────────

def test_to_decimal_plain():
    assert _to_decimal("1250") == Decimal("1250")

def test_to_decimal_with_commas():
    assert _to_decimal("1,250.50") == Decimal("1250.50")

def test_to_decimal_percent():
    assert _to_decimal("3.5%") == Decimal("3.5")

def test_to_decimal_empty():
    assert _to_decimal("") is None

def test_to_decimal_dash():
    assert _to_decimal("-") is None

def test_to_decimal_dash_value():
    assert _to_decimal("-5.0") == Decimal("-5.0")


# ── _to_int ────────────────────────────────────────────────────────────────────

def test_to_int_plain():
    assert _to_int("450") == 450

def test_to_int_with_commas():
    assert _to_int("1,000,000") == 1_000_000

def test_to_int_empty():
    assert _to_int("") is None


# ── parse_row ──────────────────────────────────────────────────────────────────

def _make_cells(ticker="MIE", open_="1200", high="1300", low="1180",
                last="1250", prev_close="1200", close="1250",
                change="+4.17%", volume="4,500", value="5,625,000",
                bid_price="1240", bid_qty="200", ask_price="1260", ask_qty="150"):
    return [ticker, open_, high, low, last, prev_close, close,
            change, volume, value, bid_price, bid_qty, ask_price, ask_qty]


def test_parse_row_valid():
    row = parse_row(_make_cells())
    assert row is not None
    assert row["ticker"] == "MIE"
    assert row["last"] == Decimal("1250")
    assert row["volume"] == 4500
    assert row["bid_price"] == Decimal("1240")
    assert row["ask_qty"] == 150


def test_parse_row_empty_bid_ask():
    cells = _make_cells(bid_price="", bid_qty="", ask_price="", ask_qty="")
    row = parse_row(cells)
    assert row is not None
    assert row["bid_price"] is None
    assert row["ask_qty"] is None


def test_parse_row_numeric_with_commas():
    cells = _make_cells(volume="1,234,567", value="1,500,000,000")
    row = parse_row(cells)
    assert row["volume"] == 1_234_567
    assert row["value"] == Decimal("1500000000")


def test_parse_row_header_skipped():
    assert parse_row(["TICKER", "OPEN", "HIGH", "LOW", "LAST", "PREV", "CLOSE",
                       "CHG%", "VOL", "VALUE", "BID", "B.QTY", "ASK", "A.QTY"]) is None


def test_parse_row_too_short():
    assert parse_row(["MIE", "1200"]) is None


def test_parse_row_empty_ticker():
    cells = _make_cells(ticker="")
    assert parse_row(cells) is None


# ── upsert_quotes (mocked DB) ──────────────────────────────────────────────────

def test_upsert_empty_rows_returns_zero():
    assert upsert_quotes([]) == 0


def test_upsert_calls_execute_per_row():
    from datetime import datetime, timezone
    rows = [
        {**parse_row(_make_cells("MIE")), "trade_time": datetime.now(timezone.utc)},
        {**parse_row(_make_cells("BDL")), "trade_time": datetime.now(timezone.utc)},
    ]

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("ingest_mse.get_db_conn", return_value=mock_conn):
        result = upsert_quotes(rows)

    assert result == 2
    # Each row triggers ENSURE_TICKER_SQL + UPSERT_SQL = 2 execute calls per row
    assert mock_cursor.execute.call_count == 4

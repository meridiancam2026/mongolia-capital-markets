"""
MSE today's-trade scraper.

Usage:
    python scripts/ingest_mse.py              # normal run — scrape and upsert
    python scripts/ingest_mse.py --discover   # dump page HTML to logs/mse_page_dump.html
    python scripts/ingest_mse.py --dry-run    # scrape and print rows, skip DB write
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── environment ────────────────────────────────────────────────────────────────
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_project_root / "logs" / "ingest_mse.log"),
    ],
)
log = logging.getLogger(__name__)

MSE_URL = "https://mse.mn/mn/markets/todaytrade"
TABLE_ROW_SELECTOR = "table tbody tr"
PAGE_TIMEOUT_MS = 20_000

# Column index mapping — verify with --discover if rows look wrong
# Expected MSE today's-trade columns (0-indexed):
#   0: ticker  1: open  2: high  3: low  4: last  5: prev_close
#   6: close   7: change_pct  8: volume  9: value
#   10: bid_price  11: bid_qty  12: ask_price  13: ask_qty
COL = {
    "ticker": 0, "open": 1, "high": 2, "low": 3, "last": 4,
    "prev_close": 5, "change_pct": 7, "volume": 8, "value": 9,
    "bid_price": 10, "bid_qty": 11, "ask_price": 12, "ask_qty": 13,
}


# ── helpers ────────────────────────────────────────────────────────────────────
def _to_decimal(text: str) -> Decimal | None:
    cleaned = text.strip().replace(",", "").replace("%", "")
    if not cleaned or cleaned in ("-", "—", "N/A"):
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _to_int(text: str) -> int | None:
    cleaned = text.strip().replace(",", "")
    if not cleaned or cleaned in ("-", "—"):
        return None
    try:
        return int(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


def parse_row(cells: list[str]) -> dict | None:
    """Extract a quote dict from a list of cell text values. Returns None for header/empty rows."""
    if len(cells) < 10:
        return None
    ticker = cells[COL["ticker"]].strip().upper()
    if not ticker or ticker in ("TICKER", "№", "#"):
        return None
    return {
        "ticker": ticker,
        "open": _to_decimal(cells[COL["open"]]),
        "high": _to_decimal(cells[COL["high"]]),
        "low": _to_decimal(cells[COL["low"]]),
        "last": _to_decimal(cells[COL["last"]]),
        "prev_close": _to_decimal(cells[COL["prev_close"]]),
        "change_pct": _to_decimal(cells[COL["change_pct"]]) if len(cells) > COL["change_pct"] else None,
        "volume": _to_int(cells[COL["volume"]]) if len(cells) > COL["volume"] else None,
        "value": _to_decimal(cells[COL["value"]]) if len(cells) > COL["value"] else None,
        "bid_price": _to_decimal(cells[COL["bid_price"]]) if len(cells) > COL["bid_price"] else None,
        "bid_qty": _to_int(cells[COL["bid_qty"]]) if len(cells) > COL["bid_qty"] else None,
        "ask_price": _to_decimal(cells[COL["ask_price"]]) if len(cells) > COL["ask_price"] else None,
        "ask_qty": _to_int(cells[COL["ask_qty"]]) if len(cells) > COL["ask_qty"] else None,
        "trade_time": datetime.now(timezone.utc),
    }


# ── scraper ────────────────────────────────────────────────────────────────────
def scrape_quotes(discover: bool = False) -> list[dict]:
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/snap/bin/chromium")
    rows: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path, headless=True)
        page = browser.new_page()
        try:
            page.goto(MSE_URL, timeout=PAGE_TIMEOUT_MS)
            page.wait_for_selector(TABLE_ROW_SELECTOR, timeout=PAGE_TIMEOUT_MS)
        except PWTimeout:
            log.warning("Timed out waiting for MSE table — page may have changed or be unavailable")
            browser.close()
            return []

        if discover:
            dump_path = _project_root / "logs" / "mse_page_dump.html"
            dump_path.write_text(page.content(), encoding="utf-8")
            log.info("Discover mode: page HTML saved to %s", dump_path)
            log.info("Open that file in a browser or text editor to verify column indices in COL dict")
            browser.close()
            return []

        tr_elements = page.query_selector_all(TABLE_ROW_SELECTOR)
        for tr in tr_elements:
            cells = [td.inner_text() for td in tr.query_selector_all("td")]
            row = parse_row(cells)
            if row:
                rows.append(row)

        browser.close()

    log.info("Scraped %d quote rows from MSE", len(rows))
    return rows


# ── database ───────────────────────────────────────────────────────────────────
def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


UPSERT_SQL = """
INSERT INTO quotes (
    ticker, trade_time, open, high, low, last, prev_close, change_pct,
    volume, value, bid_price, bid_qty, ask_price, ask_qty
) VALUES (
    %(ticker)s, %(trade_time)s, %(open)s, %(high)s, %(low)s, %(last)s,
    %(prev_close)s, %(change_pct)s, %(volume)s, %(value)s,
    %(bid_price)s, %(bid_qty)s, %(ask_price)s, %(ask_qty)s
)
ON CONFLICT (ticker, trade_time) DO UPDATE SET
    last       = EXCLUDED.last,
    high       = EXCLUDED.high,
    low        = EXCLUDED.low,
    volume     = EXCLUDED.volume,
    value      = EXCLUDED.value,
    bid_price  = EXCLUDED.bid_price,
    bid_qty    = EXCLUDED.bid_qty,
    ask_price  = EXCLUDED.ask_price,
    ask_qty    = EXCLUDED.ask_qty
"""

ENSURE_TICKER_SQL = """
INSERT INTO securities (ticker) VALUES (%s)
ON CONFLICT (ticker) DO NOTHING
"""


def upsert_quotes(rows: list[dict]) -> int:
    if not rows:
        return 0
    conn = get_db_conn()
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(ENSURE_TICKER_SQL, (row["ticker"],))
                    cur.execute(UPSERT_SQL, row)
                    inserted += 1
    finally:
        conn.close()
    return inserted


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape MSE today's-trade quotes")
    parser.add_argument("--discover", action="store_true", help="Dump page HTML and exit (no DB write)")
    parser.add_argument("--dry-run", action="store_true", help="Print rows without writing to DB")
    args = parser.parse_args()

    rows = scrape_quotes(discover=args.discover)
    if args.discover or not rows:
        sys.exit(0)

    if args.dry_run:
        for r in rows:
            print(r)
        log.info("Dry run — %d rows found, none inserted", len(rows))
        sys.exit(0)

    inserted = upsert_quotes(rows)
    log.info("Upserted %d rows into quotes table", inserted)


if __name__ == "__main__":
    main()

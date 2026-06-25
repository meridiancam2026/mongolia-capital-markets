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

MSE_URL = "https://mse.mn/todays-trade"
TABLE_ROW_SELECTOR = "table tbody tr"
PAGE_TIMEOUT_MS = 20_000

# Column index mapping — confirmed from live page dump 2026-06-25
# MSE today's-trade columns (0-indexed, 15 cells per row):
#   0: Симбол (ticker)
#   1: Нээлт (open)        2: Дээд (high)          3: Доод (low)
#   4: Сүүлийн ханш (last) 5: Өмнөх өдрийн хаалт (prev_close)
#   6: Хаалтын ханш (close) 7: Өөрчлөлт (change)  8: Өөрчлөлт/% (change_pct)
#   9: Ширхэг (volume)     10: Нийт мөнгөн дүн (value)
#   11: Авах тоо (bid_qty) 12: Авах үнэ (bid_price)
#   13: Зарах тоо (ask_qty) 14: Зарах үнэ (ask_price)
COL = {
    "ticker": 0, "open": 1, "high": 2, "low": 3, "last": 4,
    "prev_close": 5, "close": 6, "change": 7, "change_pct": 8,
    "volume": 9, "value": 10,
    "bid_qty": 11, "bid_price": 12, "ask_qty": 13, "ask_price": 14,
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
    if len(cells) < 11:
        return None
    ticker = cells[COL["ticker"]].strip().upper()
    if not ticker or ticker in ("TICKER", "СИМБОЛ", "№", "#"):
        return None

    def get(key):
        idx = COL[key]
        return cells[idx] if len(cells) > idx else ""

    return {
        "ticker": ticker,
        "open": _to_decimal(get("open")),
        "high": _to_decimal(get("high")),
        "low": _to_decimal(get("low")),
        "last": _to_decimal(get("last")),
        "prev_close": _to_decimal(get("prev_close")),
        "close": _to_decimal(get("close")),
        "change": _to_decimal(get("change")),
        "change_pct": _to_decimal(get("change_pct")),
        "volume": _to_int(get("volume")),
        "value": _to_decimal(get("value")),
        "bid_qty": _to_int(get("bid_qty")),
        "bid_price": _to_decimal(get("bid_price")),
        "ask_qty": _to_int(get("ask_qty")),
        "ask_price": _to_decimal(get("ask_price")),
        "trade_time": datetime.now(timezone.utc),
    }


# ── scraper ────────────────────────────────────────────────────────────────────
def scrape_quotes(discover: bool = False) -> list[dict]:
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/snap/bin/chromium")
    rows: list[dict] = []
    dump_path = _project_root / "logs" / "mse_page_dump.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path, headless=True)
        page = browser.new_page()

        # In discover mode: navigate and wait for network to settle, then dump
        # regardless of whether the table selector matched.
        if discover:
            try:
                # MSE uses Next.js SSR — data is in initial HTML, no need for networkidle
                page.goto(MSE_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            except PWTimeout:
                log.warning("Page did not load within timeout — dumping whatever loaded")
            dump_path.write_text(page.content(), encoding="utf-8")
            log.info("Discover mode: HTML saved to %s (%d bytes)", dump_path, dump_path.stat().st_size)
            log.info("Search the file for 'tbody', 'tr', 'td' or the first ticker symbol to find the table structure")
            browser.close()
            return []

        # Normal / dry-run mode: SSR page — data is in initial HTML
        try:
            page.goto(MSE_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            page.wait_for_selector(TABLE_ROW_SELECTOR, timeout=10_000)
        except PWTimeout:
            log.warning("Timed out waiting for MSE table — page may have changed or be unavailable")
            # Save HTML for debugging even in normal mode
            dump_path.write_text(page.content(), encoding="utf-8")
            log.warning("Page HTML saved to %s for inspection", dump_path)
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
    ticker, trade_time, open, high, low, last, prev_close, close, change, change_pct,
    volume, value, bid_qty, bid_price, ask_qty, ask_price
) VALUES (
    %(ticker)s, %(trade_time)s, %(open)s, %(high)s, %(low)s, %(last)s,
    %(prev_close)s, %(close)s, %(change)s, %(change_pct)s, %(volume)s, %(value)s,
    %(bid_qty)s, %(bid_price)s, %(ask_qty)s, %(ask_price)s
)
ON CONFLICT (ticker, trade_time) DO UPDATE SET
    last       = EXCLUDED.last,
    close      = EXCLUDED.close,
    high       = EXCLUDED.high,
    low        = EXCLUDED.low,
    change     = EXCLUDED.change,
    change_pct = EXCLUDED.change_pct,
    volume     = EXCLUDED.volume,
    value      = EXCLUDED.value,
    bid_qty    = EXCLUDED.bid_qty,
    bid_price  = EXCLUDED.bid_price,
    ask_qty    = EXCLUDED.ask_qty,
    ask_price  = EXCLUDED.ask_price
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

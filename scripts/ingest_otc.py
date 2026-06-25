"""
MASD M-OTC bond market data scraper.

The MASD market-data page is a JS-rendered dashboard showing:
  - Top-5 most active bonds today (bond name + total value)
  - Top-5 most active brokers today (broker name + total value)
  - Market summary: secondary market total, primary market total, OTC bond balance

Individual trade rows (price, yield per transaction) require authenticated OTC.mn
access — they are not publicly available on the MASD dashboard.

Usage:
    python scripts/ingest_otc.py              # scrape and insert
    python scripts/ingest_otc.py --discover   # dump page HTML to logs/otc_page_dump.html
    python scripts/ingest_otc.py --dry-run    # scrape and print rows, skip DB write
"""
import argparse
import logging
import os
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from bs4 import BeautifulSoup
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
        logging.FileHandler(_project_root / "logs" / "ingest_otc.log"),
    ],
)
log = logging.getLogger(__name__)

OTC_URL = "https://masd.mn/otc/market-data"
PAGE_TIMEOUT_MS = 25_000

# MASD page table structure (confirmed from 2026-06-25 discover run):
# Table 0: Top-5 Brokers  [rank, broker_name, value_tbm]
# Table 1: Top-5 Bonds    [rank, bond_name, value_tbm]
BOND_TABLE_INDEX = 1


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


def _to_date(text: str) -> date | None:
    from datetime import datetime
    cleaned = text.strip()
    if not cleaned or cleaned in ("-", "—"):
        return None
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    log.warning("Could not parse date %r — using today", cleaned)
    return date.today()


def _parse_tbm_value(text: str) -> Decimal | None:
    """Parse MASD value strings like '₮25.0ТБ' (25 billion MNT) or '₮141.7ТБ'."""
    cleaned = text.strip().replace("₮", "").replace(",", "").replace(" ", "")
    if "ТБ" in cleaned:
        num = cleaned.replace("ТБ", "").strip()
        try:
            return Decimal(num) * Decimal("1000000000")
        except InvalidOperation:
            return None
    # Fallback: plain numeric
    return _to_decimal(cleaned)


def parse_row(cells: list[str]) -> dict | None:
    """Extract a bond record from Top-5 Bonds table cells [rank, name, value].

    Returns None for header rows or rows without a bond name.
    """
    if len(cells) < 3:
        return None
    bond_name = cells[1].strip()
    if not bond_name or bond_name.upper() in ("НЭРШИЛ", "BOND", "БОНД", "#", "№"):
        return None

    return {
        "bond_name": bond_name,
        "price": None,
        "yield": None,
        "volume": None,
        "value": _parse_tbm_value(cells[2]),
        "trade_date": date.today(),
        "market_type": None,
    }


def parse_market_summary(soup: "BeautifulSoup") -> list[dict]:
    """Extract MASD market summary stats from the rendered page.

    Summary cards use Mongolian 'тэрбум' (billion) format: '₮12.5 тэрбум'.
    Bond leaderboard tables use the compact 'ТБ' abbreviation: '₮25.0ТБ'.
    """
    import re
    today = date.today()
    seen: set[str] = set()
    results = []

    # Keywords map Mongolian text → indicator name
    KEYWORDS = {
        "Хоёрдогч зах зээл": "MASD_SECONDARY_MARKET_MNT",
        "Анхдагч зах зээл": "MASD_PRIMARY_MARKET_MNT",
        "Нийт ОТС бондын үлдэгдэл": "MASD_OTC_BOND_BALANCE_MNT",
    }

    # Pattern: '₮12.5 тэрбум' (summary cards) — NOT '₮25.0ТБ' (bond leaderboard)
    TERBUM_RE = re.compile(r"₮\s*([\d.]+)\s*тэрбум")

    for div in soup.find_all("div"):
        text = div.get_text(strip=True)
        # Only process divs containing exactly ONE of the keywords — this targets
        # individual stat cards, not the parent grid div that contains all keywords.
        matching = [kw for kw in KEYWORDS if kw in text]
        if len(matching) != 1:
            continue
        keyword = matching[0]
        indicator = KEYWORDS[keyword]
        if indicator in seen:
            continue
        match = TERBUM_RE.search(text)
        if match:
            try:
                val = Decimal(match.group(1)) * Decimal("1000000000")
                results.append({
                    "indicator": indicator,
                    "value": val,
                    "reference_date": today,
                    "source": "MASD",
                })
                seen.add(indicator)
            except InvalidOperation:
                pass

    return results


# ── scraper ────────────────────────────────────────────────────────────────────
def scrape_otc_data(discover: bool = False) -> tuple[list[dict], list[dict]]:
    """Returns (otc_rows for otc_trades, macro_rows for macro table)."""
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/snap/bin/chromium")
    dump_path = _project_root / "logs" / "otc_page_dump.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path, headless=True)
        page = browser.new_page()

        try:
            # MASD is client-side rendered — wait for network to settle
            page.goto(OTC_URL, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
        except PWTimeout:
            log.warning("Page did not reach networkidle — dumping whatever loaded")

        html = page.content()
        browser.close()

    if discover:
        dump_path.write_text(html, encoding="utf-8")
        log.info("Discover mode: HTML saved to %s (%d bytes)", dump_path, dump_path.stat().st_size)
        return [], []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    if len(tables) <= BOND_TABLE_INDEX:
        log.warning("Expected at least %d table(s), found %d — page structure may have changed",
                    BOND_TABLE_INDEX + 1, len(tables))
        dump_path.write_text(html, encoding="utf-8")
        log.warning("Page HTML saved to %s for inspection", dump_path)
        return [], []

    # Parse bond leaderboard (second table)
    otc_rows = []
    bond_table = tables[BOND_TABLE_INDEX]
    for tr in bond_table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        row = parse_row(cells)
        if row:
            otc_rows.append(row)

    # Parse market summary stats → macro rows
    macro_rows = parse_market_summary(soup)

    log.info("Scraped %d bond leaderboard rows and %d market summary rows from MASD",
             len(otc_rows), len(macro_rows))
    return otc_rows, macro_rows


# ── database ───────────────────────────────────────────────────────────────────
def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


INSERT_OTC_SQL = """
INSERT INTO otc_trades (bond_name, price, yield, volume, value, trade_date, market_type)
VALUES (%(bond_name)s, %(price)s, %(yield)s, %(volume)s, %(value)s, %(trade_date)s, %(market_type)s)
ON CONFLICT (bond_name, trade_date) DO UPDATE SET
    value = EXCLUDED.value
"""

UPSERT_MACRO_SQL = """
INSERT INTO macro (indicator, value, reference_date, source)
VALUES (%(indicator)s, %(value)s, %(reference_date)s, %(source)s)
ON CONFLICT (indicator, reference_date) DO UPDATE SET
    value = EXCLUDED.value, source = EXCLUDED.source
"""


def insert_otc_trades(rows: list[dict]) -> int:
    if not rows:
        return 0
    conn = get_db_conn()
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(INSERT_OTC_SQL, row)
                    inserted += 1
    finally:
        conn.close()
    return inserted


def insert_macro(rows: list[dict]) -> int:
    if not rows:
        return 0
    conn = get_db_conn()
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(UPSERT_MACRO_SQL, row)
                    inserted += 1
    finally:
        conn.close()
    return inserted


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape MASD M-OTC bond market data")
    parser.add_argument("--discover", action="store_true",
                        help="Dump page HTML and exit (no DB write)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print rows without writing to DB")
    args = parser.parse_args()

    otc_rows, macro_rows = scrape_otc_data(discover=args.discover)
    if args.discover:
        sys.exit(0)

    if not otc_rows and not macro_rows:
        log.warning("No rows scraped — check MASD page or run --discover")
        sys.exit(0)

    if args.dry_run:
        print("=== OTC bond leaderboard ===")
        for r in otc_rows:
            print(r)
        print("=== Market summary (macro) ===")
        for r in macro_rows:
            print(r)
        log.info("Dry run — %d OTC + %d macro rows found, none inserted",
                 len(otc_rows), len(macro_rows))
        sys.exit(0)

    n_otc = insert_otc_trades(otc_rows)
    n_macro = insert_macro(macro_rows)
    log.info("Upserted %d OTC bond rows and %d macro summary rows", n_otc, n_macro)


if __name__ == "__main__":
    main()

"""
MASD OTC Bond Registry scraper.

Scrapes the publicly accessible bond registry at masd.mn/otc/board — 316 bonds
with board category, sector, issue date, currency, maturity, coupon rate,
underwriter, and status. No login or Playwright required (page is SSR).

Usage:
    python scripts/ingest_otc_registry.py
    python scripts/ingest_otc_registry.py --dry-run
"""
import argparse
import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

REGISTRY_URL = "https://masd.mn/otc/board"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MongoliaCapitalMarkets/1.0)"}

# Mongolian column headers → field names
COLUMN_MAP = {
    "Самбар":       "board_category",
    "Бондын нэр":   "bond_name",
    "Салбар":       "sector",
    "Огноо":        "issue_date",
    "Валют":        "currency",
    "Хугацаа":      "maturity_months",
    "Хүү":          "coupon_rate_raw",
    "Андеррайтер":  "underwriter",
    "Төлөв":        "status",
}

UPSERT_SQL = """
INSERT INTO otc_bond_registry
    (bond_name, board_category, sector, issue_date, currency,
     maturity_months, coupon_rate_raw, coupon_rate, underwriter, status, scraped_date)
VALUES
    (%(bond_name)s, %(board_category)s, %(sector)s, %(issue_date)s, %(currency)s,
     %(maturity_months)s, %(coupon_rate_raw)s, %(coupon_rate)s, %(underwriter)s,
     %(status)s, %(scraped_date)s)
ON CONFLICT (bond_name) DO UPDATE SET
    board_category  = EXCLUDED.board_category,
    sector          = EXCLUDED.sector,
    issue_date      = EXCLUDED.issue_date,
    currency        = EXCLUDED.currency,
    maturity_months = EXCLUDED.maturity_months,
    coupon_rate_raw = EXCLUDED.coupon_rate_raw,
    coupon_rate     = EXCLUDED.coupon_rate,
    underwriter     = EXCLUDED.underwriter,
    status          = EXCLUDED.status,
    scraped_date    = EXCLUDED.scraped_date
"""


def _parse_date(text: str) -> date | None:
    cleaned = text.strip()
    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _parse_maturity(text: str) -> int | None:
    """Extract integer months from strings like '48 сар', '24', '—'."""
    cleaned = text.strip().replace("сар", "").replace("month", "").strip()
    if not cleaned or cleaned in ("-", "—"):
        return None
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _parse_coupon(text: str) -> tuple[str | None, Decimal | None]:
    """Parse coupon strings like '19-20%', '19.5%', '—'.
    Returns (raw_text, midpoint_decimal).
    """
    cleaned = text.strip().replace("%", "").strip()
    if not cleaned or cleaned in ("-", "—"):
        return None, None
    # Range like "19-20"
    range_match = re.match(r"([\d.]+)\s*[-–]\s*([\d.]+)", cleaned)
    if range_match:
        lo = Decimal(range_match.group(1))
        hi = Decimal(range_match.group(2))
        return text.strip(), ((lo + hi) / 2).quantize(Decimal("0.01"))
    # Single value
    try:
        return text.strip(), Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return text.strip(), None


def _normalize_currency(text: str) -> str:
    t = text.strip().lower()
    if "tugrik" in t or "мнт" in t or "төгрөг" in t:
        return "MNT"
    if "usd" in t or "dollar" in t or "ам.доллар" in t:
        return "USD"
    return text.strip()[:10]


def fetch_bonds() -> list[dict]:
    log.info("Fetching %s", REGISTRY_URL)
    resp = requests.get(REGISTRY_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        log.error("No <table> found — page may require JS. Try running with Playwright.")
        return []

    # Detect column order from headers
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    log.info("Detected columns: %s", headers)

    col_index = {}
    for i, h in enumerate(headers):
        for mn, field in COLUMN_MAP.items():
            if mn in h:
                col_index[field] = i
                break

    if "bond_name" not in col_index:
        log.error("Could not find 'Бондын нэр' column. Headers found: %s", headers)
        return []

    today = date.today()
    rows = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if not cells:
            continue

        def cell(field: str) -> str:
            idx = col_index.get(field)
            return cells[idx].strip() if idx is not None and idx < len(cells) else ""

        bond_name = cell("bond_name")
        if not bond_name or bond_name in ("Бондын нэр", "Bond Name"):
            continue

        raw_coupon = cell("coupon_rate_raw")
        coupon_raw, coupon_dec = _parse_coupon(raw_coupon)

        rows.append({
            "bond_name":       bond_name,
            "board_category":  cell("board_category") or None,
            "sector":          cell("sector") or None,
            "issue_date":      _parse_date(cell("issue_date")),
            "currency":        _normalize_currency(cell("currency")) or None,
            "maturity_months": _parse_maturity(cell("maturity_months")),
            "coupon_rate_raw": coupon_raw,
            "coupon_rate":     coupon_dec,
            "underwriter":     cell("underwriter") or None,
            "status":          cell("status") or None,
            "scraped_date":    today,
        })

    log.info("Parsed %d bond rows", len(rows))
    return rows


def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL") or os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


def upsert(rows: list[dict]) -> int:
    conn = get_db_conn()
    count = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(UPSERT_SQL, row)
                    count += 1
    finally:
        conn.close()
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = fetch_bonds()
    if not rows:
        log.warning("No bonds scraped")
        return

    if args.dry_run:
        for r in rows:
            print(r)
        log.info("Dry run — %d rows, none inserted", len(rows))
        return

    n = upsert(rows)
    log.info("Done — %d bonds upserted into otc_bond_registry", n)


if __name__ == "__main__":
    main()

"""
MSE securities master list updater.

Scrapes the MSE company listing page and upserts into the securities table.
Run once on initial setup, then weekly via cron.

Usage:
    python scripts/ingest_mse_securities.py
    python scripts/ingest_mse_securities.py --discover   # dump HTML for selector verification
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_project_root / "logs" / "ingest_mse_securities.log"),
    ],
)
log = logging.getLogger(__name__)

# MSE company listing page — verify URL with --discover
MSE_COMPANY_URL = "https://mse.mn/mn/company/index"
TABLE_ROW_SELECTOR = "table tbody tr"
PAGE_TIMEOUT_MS = 20_000

# Column mapping — verify with --discover
# Expected: 0: ticker/symbol, 1: company name, 2: sector (may vary)
COL = {"ticker": 0, "name": 1, "sector": 2}


def scrape_securities(discover: bool = False) -> list[dict]:
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/snap/bin/chromium")
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path, headless=True)
        page = browser.new_page()
        try:
            page.goto(MSE_COMPANY_URL, timeout=PAGE_TIMEOUT_MS)
            page.wait_for_selector(TABLE_ROW_SELECTOR, timeout=PAGE_TIMEOUT_MS)
        except PWTimeout:
            log.warning("Timed out waiting for MSE company listing page")
            browser.close()
            return []

        if discover:
            dump_path = _project_root / "logs" / "mse_securities_dump.html"
            dump_path.write_text(page.content(), encoding="utf-8")
            log.info("Discover mode: HTML saved to %s", dump_path)
            browser.close()
            return []

        for tr in page.query_selector_all(TABLE_ROW_SELECTOR):
            cells = [td.inner_text().strip() for td in tr.query_selector_all("td")]
            if len(cells) < 2:
                continue
            ticker = cells[COL["ticker"]].upper()
            if not ticker or ticker in ("TICKER", "SYMBOL", "№"):
                continue
            results.append({
                "ticker": ticker,
                "name": cells[COL["name"]] if len(cells) > COL["name"] else None,
                "sector": cells[COL["sector"]] if len(cells) > COL["sector"] else None,
            })

        browser.close()

    log.info("Found %d securities", len(results))
    return results


def upsert_securities(rows: list[dict]) -> int:
    if not rows:
        return 0
    url = os.environ.get("DATABASE_SYNC_URL", "").replace("postgresql+psycopg2://", "postgresql://", 1)
    conn = psycopg2.connect(url)
    count = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for r in rows:
                    cur.execute("""
                        INSERT INTO securities (ticker, name, sector)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (ticker) DO UPDATE
                        SET name = EXCLUDED.name, sector = EXCLUDED.sector
                    """, (r["ticker"], r["name"], r["sector"]))
                    count += 1
    finally:
        conn.close()
    return count


def main():
    parser = argparse.ArgumentParser(description="Update MSE securities master list")
    parser.add_argument("--discover", action="store_true")
    args = parser.parse_args()

    rows = scrape_securities(discover=args.discover)
    if args.discover or not rows:
        sys.exit(0)

    n = upsert_securities(rows)
    log.info("Upserted %d securities", n)


if __name__ == "__main__":
    main()

"""
Commodity prices ingestion — copper, gold, and coal demand proxy.

Usage:
    python scripts/ingest_commodities.py                # fetch via yfinance
    python scripts/ingest_commodities.py --dry-run      # print rows without DB write

Requires: pip install yfinance pandas

Data source: Yahoo Finance via yfinance (free, no API key required).

Symbols used:
  HG=F     — COMEX copper front-month futures (USD/pound → converted to USD/MT)
  GC=F     — COMEX gold front-month futures (USD/troy oz)
  1171.HK  — Yankuang Energy Group (HKD/share); used as China coal demand proxy
              since Newcastle coal futures (NCFF=F) are not listed on Yahoo Finance.
              Yankuang is one of China's largest coal producers and a key buyer of
              Mongolian coking coal.

Indicator codes stored in macro table:
  COMMODITY_COPPER_USD_MT    — Copper, USD/metric ton
  COMMODITY_GOLD_USD_OZ      — Gold, USD/troy oz
  COMMODITY_COAL_PROXY_HKD  — Yankuang Energy HKD/share (coal demand proxy)
"""
import argparse
import logging
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# ── environment ────────────────────────────────────────────────────────────────
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_project_root / "logs" / "ingest_commodities.log"),
    ],
)
log = logging.getLogger(__name__)

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print(
        "ERROR: yfinance and pandas are required.\n"
        "Run:  pip install yfinance pandas\n"
        "Then retry."
    )
    sys.exit(1)

# 1 metric ton = 2204.6226 lbs; HG=F is quoted in USD/lb → multiply for USD/MT
LB_TO_MT = 2204.6226

# indicator code → (YF symbol, price multiplier, description)
COMMODITY_SOURCES: dict[str, tuple[str, float, str]] = {
    "COMMODITY_COPPER_USD_MT":  ("HG=F",    LB_TO_MT, "COMEX copper $/lb → $/MT"),
    "COMMODITY_GOLD_USD_OZ":    ("GC=F",    1.0,       "COMEX gold $/troy oz"),
    "COMMODITY_COAL_PROXY_HKD": ("1171.HK", 1.0,       "Yankuang Energy HKD/share (coal demand proxy)"),
}


# ── yfinance fetcher ───────────────────────────────────────────────────────────
def fetch_yf_commodity(indicator: str, symbol: str, multiplier: float) -> list[dict]:
    """Fetch ~24 months of monthly closing prices via yfinance.

    yfinance manages Yahoo Finance session auth internally, which avoids the
    429 rate-limit errors that occur with raw HTTP requests to the chart API.
    Returns empty list if the symbol has no data (e.g. NCFF=F not listed).
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y", interval="1mo", auto_adjust=False)
    except Exception as exc:
        log.error("yfinance fetch failed for %s (%s): %s", indicator, symbol, exc)
        return []

    if hist is None or hist.empty:
        log.warning(
            "yfinance returned empty history for %s (%s) — symbol may not be listed",
            indicator, symbol,
        )
        return []

    rows = []
    for ts, row in hist.iterrows():
        close = row.get("Close")
        if close is None or pd.isna(close):
            continue
        ref_date = date(ts.year, ts.month, 1)
        price = Decimal(str(round(float(close) * multiplier, 2)))
        rows.append({
            "indicator": indicator,
            "value": price,
            "reference_date": ref_date,
            "source": "Yahoo Finance",
        })

    rows.sort(key=lambda r: r["reference_date"])
    log.info("Fetched %d rows for %s (%s)", len(rows), indicator, symbol)
    return rows


def fetch_all_commodities() -> list[dict]:
    rows: list[dict] = []
    for indicator, (symbol, multiplier, _desc) in COMMODITY_SOURCES.items():
        rows.extend(fetch_yf_commodity(indicator, symbol, multiplier))
    return rows


# ── database ───────────────────────────────────────────────────────────────────
def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


UPSERT_SQL = """
INSERT INTO macro (indicator, value, reference_date, source)
VALUES (%(indicator)s, %(value)s, %(reference_date)s, %(source)s)
ON CONFLICT (indicator, reference_date) DO UPDATE SET
    value  = EXCLUDED.value,
    source = EXCLUDED.source
"""


def upsert_macro(rows: list[dict]) -> int:
    if not rows:
        return 0
    conn = get_db_conn()
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(UPSERT_SQL, row)
                    inserted += 1
    finally:
        conn.close()
    return inserted


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ingest commodity prices (copper, gold, coal) via yfinance"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print rows without writing to DB")
    args = parser.parse_args()

    rows = fetch_all_commodities()

    if not rows:
        log.warning("No commodity rows fetched — check yfinance installation and network")
        sys.exit(1)

    if args.dry_run:
        for r in rows:
            print(r)
        log.info("Dry run — %d rows found, none inserted", len(rows))
        sys.exit(0)

    inserted = upsert_macro(rows)
    log.info("Upserted %d commodity rows into macro table", inserted)


if __name__ == "__main__":
    main()

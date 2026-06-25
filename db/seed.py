"""
Static MSE securities seed.

Inserts a hardcoded list of MSE tickers into the securities table so a freshly
created database has entries before the first live scraper run. Safe to re-run —
uses ON CONFLICT DO NOTHING.

Usage:
    python db/seed.py
    python db/seed.py --dry-run   # print tickers without inserting
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# Confirmed MSE-listed tickers from 2026-06-25 live scrape (44 tickers)
TICKERS = [
    "AARD", "ADB",  "ADU",  "AIC",  "APU",  "BAN",  "BDL",  "BDS",
    "BODI", "CUMN", "ERDN", "ETR",  "GAZR", "GLMT", "GOV",  "HBO",
    "HRM",  "HSR",  "INV",  "ITLS", "JTB",  "KHAN", "LEND", "MBG",
    "MBW",  "MFC",  "MGLA", "MLG",  "MMX",  "MNDL", "MNP",  "MSE",
    "NEH",  "QPAY", "RMC",  "SBM",  "SEND", "SUU",  "TAND", "TDB",
    "TGI",  "TTL",  "TUM",  "XAC",
]

INSERT_SQL = "INSERT INTO securities (ticker) VALUES (%s) ON CONFLICT (ticker) DO NOTHING"


def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


def seed(tickers: list[str]) -> tuple[int, int]:
    conn = get_db_conn()
    inserted = skipped = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for ticker in tickers:
                    cur.execute(INSERT_SQL, (ticker,))
                    if cur.rowcount:
                        inserted += 1
                    else:
                        skipped += 1
    finally:
        conn.close()
    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(description="Seed securities table with static MSE ticker list")
    parser.add_argument("--dry-run", action="store_true", help="Print tickers without inserting")
    args = parser.parse_args()

    if args.dry_run:
        for t in TICKERS:
            print(t)
        log.info("Dry run — %d tickers listed, none inserted", len(TICKERS))
        sys.exit(0)

    inserted, skipped = seed(TICKERS)
    log.info("Done: %d inserted, %d skipped (already existed)", inserted, skipped)


if __name__ == "__main__":
    main()

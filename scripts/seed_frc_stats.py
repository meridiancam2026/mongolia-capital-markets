"""
One-time loader: reads data/frc_stats.csv and inserts rows into regulatory_stats.

Safe to re-run — uses ON CONFLICT DO NOTHING so existing rows are skipped.

Usage:
    python scripts/seed_frc_stats.py
    python scripts/seed_frc_stats.py --dry-run   # print rows without inserting
"""
import argparse
import csv
import logging
import os
import sys
from decimal import Decimal, InvalidOperation
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

CSV_PATH = _project_root / "data" / "frc_stats.csv"

INSERT_SQL = """
INSERT INTO regulatory_stats (indicator, value, unit, reference_year, source, notes)
VALUES (%(indicator)s, %(value)s, %(unit)s, %(reference_year)s, %(source)s, %(notes)s)
ON CONFLICT (indicator, reference_year) DO NOTHING
"""


def load_csv() -> list[dict]:
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                value = Decimal(row["value"])
            except (InvalidOperation, KeyError):
                log.warning("Could not parse value for %s: %r", row.get("indicator"), row.get("value"))
                value = None
            try:
                ref_year = int(row["reference_year"])
            except (ValueError, KeyError):
                log.warning("Could not parse reference_year for %s", row.get("indicator"))
                continue
            rows.append({
                "indicator": row["indicator"],
                "value": value,
                "unit": row.get("unit"),
                "reference_year": ref_year,
                "source": row.get("source"),
                "notes": row.get("notes"),
            })
    return rows


def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


def seed(rows: list[dict]) -> tuple[int, int]:
    conn = get_db_conn()
    inserted = skipped = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(INSERT_SQL, row)
                    if cur.rowcount:
                        inserted += 1
                    else:
                        skipped += 1
    finally:
        conn.close()
    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(description="Seed regulatory_stats from data/frc_stats.csv")
    parser.add_argument("--dry-run", action="store_true", help="Print rows without inserting")
    args = parser.parse_args()

    rows = load_csv()
    log.info("Loaded %d rows from %s", len(rows), CSV_PATH)

    if args.dry_run:
        for r in rows:
            print(r)
        sys.exit(0)

    inserted, skipped = seed(rows)
    log.info("Done: %d inserted, %d skipped (already existed)", inserted, skipped)


if __name__ == "__main__":
    main()

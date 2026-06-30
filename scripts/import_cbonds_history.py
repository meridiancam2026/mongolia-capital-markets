"""
Import Cbonds bond search CSV export into bond_price_history.

The CSV has ~40 metadata columns followed by one column per calendar day
(header format DD/MM/YYYY) containing yield % values (e.g. "6.03%").

Usage:
    python scripts/import_cbonds_history.py bondsearch_30_06_2026.csv
    python scripts/import_cbonds_history.py bondsearch_30_06_2026.csv --dry-run
"""
import argparse
import csv
import logging
import os
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

UPSERT_SQL = """
INSERT INTO bond_price_history (bond_name, cbonds_id, trade_date, price, yield, currency)
VALUES (%(bond_name)s, %(cbonds_id)s, %(trade_date)s, %(price)s, %(yield)s, %(currency)s)
ON CONFLICT (bond_name, trade_date) DO UPDATE SET
    yield     = COALESCE(EXCLUDED.yield,     bond_price_history.yield),
    price     = COALESCE(EXCLUDED.price,     bond_price_history.price),
    cbonds_id = COALESCE(EXCLUDED.cbonds_id, bond_price_history.cbonds_id)
"""


def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL") or os.environ.get("DATABASE_URL", "")
    for old, new in [
        ("postgresql+asyncpg://", "postgresql://"),
        ("postgresql+psycopg2://", "postgresql://"),
        ("postgres://", "postgresql://"),
    ]:
        if url.startswith(old):
            url = url.replace(old, new, 1)
            break
    return psycopg2.connect(url)


def _parse_yield(raw: str):
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().rstrip("%").strip()
    try:
        return Decimal(cleaned).quantize(Decimal("0.0001"))
    except InvalidOperation:
        return None


def _parse_cbonds_id(raw: str):
    if not raw or not raw.strip():
        return None
    try:
        return int(raw.replace(",", "").strip())
    except ValueError:
        return None


def _parse_date(raw: str):
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None


def load_bond_names(conn) -> dict[int, str]:
    """Map cbonds_id → bond_name from otc_trades (our canonical name source)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT cbonds_id, bond_name FROM otc_trades "
            "WHERE cbonds_id IS NOT NULL"
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def parse_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)

    # Identify which columns are dates (DD/MM/YYYY pattern)
    date_cols: list[tuple[int, object]] = []  # (col_index, date)
    meta_col = {h.strip(): i for i, h in enumerate(headers)}

    for i, h in enumerate(headers):
        d = _parse_date(h.strip())
        if d:
            date_cols.append((i, d))

    if not date_cols:
        log.error("No date columns found in header. First 5 headers: %s", headers[:5])
        sys.exit(1)

    log.info("Found %d date columns from %s to %s",
             len(date_cols), date_cols[-1][1], date_cols[0][1])

    issue_col    = meta_col.get("Issue", 0)
    isin_col     = meta_col.get("ISIN", 1)
    currency_col = meta_col.get("Currency", 16)
    cbonds_col   = meta_col.get("Cbonds ID", 38)

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for line_no, row in enumerate(reader, start=2):
            if not any(row):
                continue
            cbonds_id = _parse_cbonds_id(row[cbonds_col] if cbonds_col < len(row) else "")
            if not cbonds_id:
                continue

            csv_name  = row[issue_col].strip()  if issue_col  < len(row) else ""
            isin      = row[isin_col].strip()   if isin_col   < len(row) else ""
            currency  = row[currency_col].strip() if currency_col < len(row) else ""

            for col_idx, trade_date in date_cols:
                raw_val = row[col_idx].strip() if col_idx < len(row) else ""
                yld = _parse_yield(raw_val)
                if yld is None:
                    continue
                rows.append({
                    "cbonds_id":  cbonds_id,
                    "csv_name":   csv_name,
                    "isin":       isin,
                    "currency":   currency,
                    "trade_date": trade_date,
                    "yield":      yld,
                    "price":      None,
                })

    log.info("Parsed %d non-empty yield observations from CSV", len(rows))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="Path to the Cbonds bond search CSV export")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and print summary without writing to DB")
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        log.error("File not found: %s", csv_path)
        sys.exit(1)

    rows = parse_csv(csv_path)
    if not rows:
        log.error("No data rows parsed — check the CSV format")
        sys.exit(1)

    conn = get_db_conn()
    id_to_name = load_bond_names(conn)
    log.info("Loaded %d bond name mappings from otc_trades", len(id_to_name))

    # Enrich rows with canonical bond_name from DB; fall back to CSV name
    enriched = []
    unmatched_ids: set[int] = set()
    for r in rows:
        bond_name = id_to_name.get(r["cbonds_id"])
        if not bond_name:
            unmatched_ids.add(r["cbonds_id"])
            # Normalize CSV name (periods → commas) as fallback
            bond_name = re.sub(r'\. ', ', ', r["csv_name"]).strip()
        enriched.append({
            "bond_name":  bond_name,
            "cbonds_id":  r["cbonds_id"],
            "trade_date": r["trade_date"],
            "price":      r["price"],
            "yield":      r["yield"],
            "currency":   r["currency"],
        })

    if unmatched_ids:
        log.warning(
            "%d cbonds_id(s) not found in otc_trades (will use CSV name as fallback): %s",
            len(unmatched_ids), sorted(unmatched_ids)
        )

    # Summary
    bonds_with_data = {r["bond_name"] for r in enriched}
    log.info("Bonds with yield data: %d", len(bonds_with_data))
    for name in sorted(bonds_with_data):
        count = sum(1 for r in enriched if r["bond_name"] == name)
        log.info("  %s — %d days", name, count)

    if args.dry_run:
        log.info("Dry run — %d rows ready, none written", len(enriched))
        conn.close()
        return

    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in enriched:
                    cur.execute(UPSERT_SQL, row)
                    inserted += 1
        log.info("Done — %d yield rows upserted into bond_price_history", inserted)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

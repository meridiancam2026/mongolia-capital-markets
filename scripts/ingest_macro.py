"""
Macro data ingestion — FX rates, policy rate, inflation, and FX reserves.

Usage:
    python scripts/ingest_macro.py                               # FX via OpenExchange (default)
    python scripts/ingest_macro.py --dry-run                     # print rows without DB write
    python scripts/ingest_macro.py --source bom                  # scrape mongolbank.mn (Playwright)
    python scripts/ingest_macro.py --source bom --discover       # dump BOM HTML, do not insert
    python scripts/ingest_macro.py --source te                   # Trading Economics API (key required)
    python scripts/ingest_macro.py --source fluentax             # Fluentax API (key required)
    python scripts/ingest_macro.py --source bom_inflation        # scrape CPI YoY from BOM stats
    python scripts/ingest_macro.py --source bom_inflation --discover  # dump BOM stats HTML
    python scripts/ingest_macro.py --source bom_reserves         # scrape FX reserves from BOM
    python scripts/ingest_macro.py --source bom_reserves --discover   # dump BOM reserves HTML
    python scripts/ingest_macro.py --source wb_macro             # World Bank API: CPI + FX reserves (free, no key)

Default source 'openexchange' uses open.er-api.com — free, no API key, ~daily updates.
Switch to 'te' or 'fluentax' once API keys are obtained for official BOM data.
Use 'wb_macro' when mongolbank.mn is unreachable — World Bank provides annual Mongolia data.
"""
import argparse
import logging
import os
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
import requests
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
        logging.FileHandler(_project_root / "logs" / "ingest_macro.log"),
    ],
)
log = logging.getLogger(__name__)

# open.er-api.com — free, no key, 160+ currencies, updates daily
OPENEXCHANGE_URL = "https://open.er-api.com/v6/latest/USD"

# BOM direct URLs — requires Playwright; may time out depending on network conditions
BOM_FX_URL = "https://www.mongolbank.mn/mn/p/valuta"
BOM_POLICY_URL = "https://www.mongolbank.mn/mn/p/mprate"
BOM_STATS_URL = "https://www.mongolbank.mn/en/p/statistics"
BOM_RESERVES_URL = "https://www.mongolbank.mn/en/p/reserves"
PAGE_TIMEOUT_MS = 20_000

# Currencies to extract (ISO code → indicator name). All expressed as MNT per 1 unit.
FX_CURRENCIES = {
    "USD": "FX_USD_MNT",
    "EUR": "FX_EUR_MNT",
    "CNY": "FX_CNY_MNT",
    "RUB": "FX_RUB_MNT",
    "JPY": "FX_JPY_MNT",
    "KRW": "FX_KRW_MNT",
    "GBP": "FX_GBP_MNT",
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


def _fetch_html(url: str) -> str | None:
    """Fetch a JS-rendered page via Playwright headless Chromium."""
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/snap/bin/chromium")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_path, headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
            html = page.content()
            browser.close()
        return html
    except PWTimeout:
        log.error("Timed out loading %s", url)
        return None
    except Exception as exc:
        log.error("Failed to fetch %s: %s", url, exc)
        return None


# ── OpenExchange FX source ─────────────────────────────────────────────────────
def scrape_fx_openexchange() -> list[dict]:
    """Fetch FX rates from open.er-api.com — free, no key required."""
    try:
        resp = requests.get(OPENEXCHANGE_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        log.error("open.er-api.com request failed: %s", exc)
        return []

    if data.get("result") != "success":
        log.error("open.er-api.com returned non-success: %s", data.get("error-type"))
        return []

    rates = data["rates"]
    mnt_per_usd = Decimal(str(rates.get("MNT", 0)))
    if not mnt_per_usd:
        log.error("MNT not found in open.er-api.com response")
        return []

    today = date.today()
    rows = []

    # USD/MNT is direct from the API (base=USD)
    rows.append({
        "indicator": "FX_USD_MNT",
        "value": mnt_per_usd,
        "reference_date": today,
        "source": "open.er-api.com",
    })

    # Cross rates: X/MNT = MNT_per_USD / X_per_USD
    for iso, indicator in FX_CURRENCIES.items():
        if iso == "USD":
            continue
        x_per_usd = rates.get(iso)
        if not x_per_usd:
            continue
        cross = (mnt_per_usd / Decimal(str(x_per_usd))).quantize(Decimal("0.0001"))
        rows.append({
            "indicator": indicator,
            "value": cross,
            "reference_date": today,
            "source": "open.er-api.com",
        })

    log.info("Fetched %d FX rates from open.er-api.com", len(rows))
    return rows


# ── BOM HTML parsers (for when mongolbank.mn becomes accessible) ───────────────
def parse_fx_rates(html: str) -> list[dict]:
    """Parse BOM FX rates page HTML into macro dicts.

    BOM's FX table structure: rows with currency code + rate columns.
    Run --source bom --discover to inspect the actual HTML structure.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    today = date.today()

    tables = soup.find_all("table")
    if not tables:
        log.warning("No <table> found in BOM FX page — run --discover to inspect HTML")
        return []

    for table in tables:
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            currency_code = cells[0].strip().upper()
            if currency_code not in FX_CURRENCIES:
                continue
            rate_text = ""
            for cell in reversed(cells[1:]):
                if cell and cell not in ("-", "—"):
                    rate_text = cell
                    break
            rate = _to_decimal(rate_text)
            if rate is None:
                continue
            results.append({
                "indicator": FX_CURRENCIES[currency_code],
                "value": rate,
                "reference_date": today,
                "source": "BOM",
            })

    if not results:
        log.warning("Parsed 0 FX rates from BOM HTML — run --discover")
    return results


def parse_policy_rate(html: str) -> dict | None:
    """Parse BOM monetary policy rate page HTML into a macro dict."""
    soup = BeautifulSoup(html, "html.parser")
    today = date.today()

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "td", "span", "div"]):
        text = tag.get_text(strip=True)
        rate = _to_decimal(text)
        if rate is not None and Decimal("1") <= rate <= Decimal("30"):
            log.debug("Found candidate policy rate: %s in <%s>", rate, tag.name)
            return {
                "indicator": "POLICY_RATE",
                "value": rate,
                "reference_date": today,
                "source": "BOM",
            }

    log.warning("Could not extract policy rate from BOM HTML — run --discover")
    return None


def scrape_bom(discover: bool = False) -> list[dict]:
    """Scrape FX and policy rate directly from mongolbank.mn via Playwright."""
    fx_html = _fetch_html(BOM_FX_URL)
    policy_html = _fetch_html(BOM_POLICY_URL)

    if discover:
        if fx_html:
            p = _project_root / "logs" / "bom_fx_dump.html"
            p.write_text(fx_html, encoding="utf-8")
            log.info("BOM FX HTML saved to %s (%d bytes)", p, p.stat().st_size)
        if policy_html:
            p = _project_root / "logs" / "bom_policy_dump.html"
            p.write_text(policy_html, encoding="utf-8")
            log.info("BOM policy rate HTML saved to %s (%d bytes)", p, p.stat().st_size)
        return []

    rows: list[dict] = []
    if fx_html:
        rows.extend(parse_fx_rates(fx_html))
    else:
        log.error("Could not fetch BOM FX page — try --source openexchange instead")

    if policy_html:
        row = parse_policy_rate(policy_html)
        if row:
            rows.append(row)
    else:
        log.error("Could not fetch BOM policy rate page")

    return rows


# ── BOM inflation parser ───────────────────────────────────────────────────────
def parse_bom_inflation(html: str) -> list[dict]:
    """Extract CPI YoY % from BOM statistics page HTML.

    BOM publishes monthly CPI data. This parser scans tables for a header
    containing 'inflat' or 'cpi' and extracts the first plausible percentage.
    Run --source bom_inflation --discover to inspect the actual HTML if results
    are empty.
    """
    soup = BeautifulSoup(html, "html.parser")
    ref_date = date.today().replace(day=1)

    for table in soup.find_all("table"):
        header_texts = " ".join(
            th.get_text(strip=True).lower()
            for th in table.find_all(["th", "td"])
        )
        if not any(kw in header_texts for kw in ("inflat", "cpi", "үнэ өсөлт", "үнийн өсөлт")):
            continue
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            for cell in cells:
                val = _to_decimal(cell)
                # Mongolia CPI YoY typically 2–25%
                if val is not None and Decimal("0") < val < Decimal("25"):
                    log.info("Found candidate CPI YoY rate: %s%%", val)
                    return [{
                        "indicator": "INFLATION_CPI_YOY",
                        "value": val,
                        "reference_date": ref_date,
                        "source": "BOM",
                    }]

    log.warning("Could not extract CPI from BOM stats page — run --source bom_inflation --discover")
    return []


def scrape_bom_inflation(discover: bool = False) -> list[dict]:
    """Scrape CPI YoY inflation rate from mongolbank.mn."""
    html = _fetch_html(BOM_STATS_URL)

    if discover:
        if html:
            p = _project_root / "logs" / "bom_inflation_dump.html"
            p.write_text(html, encoding="utf-8")
            log.info("BOM inflation HTML saved to %s (%d bytes)", p, p.stat().st_size)
        return []

    if not html:
        log.error("Could not fetch BOM stats page — check network / Playwright")
        return []

    return parse_bom_inflation(html)


# ── BOM reserves parser ────────────────────────────────────────────────────────
def parse_bom_reserves(html: str) -> list[dict]:
    """Extract FX reserves (USD millions) from BOM reserves page HTML.

    BOM publishes monthly international reserve data. This parser scans tables
    for a header containing 'reserv' or 'нөөц' and extracts the first value
    in the plausible range for Mongolia (500–20,000 USD mn).
    Run --source bom_reserves --discover to inspect the actual HTML if results
    are empty.
    """
    soup = BeautifulSoup(html, "html.parser")
    ref_date = date.today().replace(day=1)

    for table in soup.find_all("table"):
        header_texts = " ".join(
            th.get_text(strip=True).lower()
            for th in table.find_all(["th", "td"])
        )
        if not any(kw in header_texts for kw in ("reserv", "нөөц", "foreign asset")):
            continue
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            for cell in cells:
                val = _to_decimal(cell)
                # Mongolia FX reserves typically 3,000–6,000 USD mn
                if val is not None and Decimal("500") < val < Decimal("20000"):
                    log.info("Found candidate FX reserves: %s USD mn", val)
                    return [{
                        "indicator": "FOREIGN_RESERVES_USD_MN",
                        "value": val,
                        "reference_date": ref_date,
                        "source": "BOM",
                    }]

    log.warning("Could not extract FX reserves from BOM page — run --source bom_reserves --discover")
    return []


def scrape_bom_reserves(discover: bool = False) -> list[dict]:
    """Scrape FX reserves (USD millions) from mongolbank.mn."""
    html = _fetch_html(BOM_RESERVES_URL)

    if discover:
        if html:
            p = _project_root / "logs" / "bom_reserves_dump.html"
            p.write_text(html, encoding="utf-8")
            log.info("BOM reserves HTML saved to %s (%d bytes)", p, p.stat().st_size)
        return []

    if not html:
        log.error("Could not fetch BOM reserves page — check network / Playwright")
        return []

    return parse_bom_reserves(html)


# ── API stubs ──────────────────────────────────────────────────────────────────
def scrape_trading_economics() -> list[dict]:
    api_key = os.environ.get("TRADING_ECONOMICS_API_KEY", "placeholder")
    if not api_key or api_key == "placeholder":
        raise NotImplementedError(
            "Set TRADING_ECONOMICS_API_KEY in .env. See data/api_notes/bom_providers.md."
        )
    raise NotImplementedError("Trading Economics integration not yet implemented")


def scrape_fluentax() -> list[dict]:
    api_key = os.environ.get("FLUENTAX_API_KEY", "placeholder")
    if not api_key or api_key == "placeholder":
        raise NotImplementedError(
            "Set FLUENTAX_API_KEY in .env. See data/api_notes/bom_providers.md."
        )
    raise NotImplementedError("Fluentax integration not yet implemented")


# ── World Bank macro source (Mongolia CPI + FX reserves) ──────────────────────
_WB_API_BASE = "https://api.worldbank.org/v2"

# indicator_code → (country_iso3, wb_series_id, scale_factor, source_label)
# FI.RES.TOTL.CD is in current USD; divide by 1e6 to store as USD millions.
_WB_MACRO_INDICATORS: dict[str, tuple[str, str, float, str]] = {
    "INFLATION_CPI_YOY":       ("MNG", "FP.CPI.TOTL.ZG", 1.0,  "World Bank"),
    "FOREIGN_RESERVES_USD_MN": ("MNG", "FI.RES.TOTL.CD",  1e-6, "World Bank"),
}


def scrape_wb_macro() -> list[dict]:
    """Fetch Mongolia CPI inflation and FX reserves from the World Bank DataBank API.

    Free, no API key required. Data is annual; reference_date stored as Jan 1 of the year.
    Preferred fallback when mongolbank.mn is unreachable via Playwright.
    """
    rows: list[dict] = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mongolia-Capital-Markets/1.0"})

    for indicator_code, (country, wb_id, scale, src) in _WB_MACRO_INDICATORS.items():
        url = f"{_WB_API_BASE}/country/{country}/indicator/{wb_id}?format=json&mrv=5"
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            log.error("World Bank API request failed for %s: %s", indicator_code, exc)
            continue

        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            log.warning("No data returned from World Bank for %s", indicator_code)
            continue

        for entry in payload[1]:
            raw = entry.get("value")
            year_str = entry.get("date", "")
            if raw is None or not year_str:
                continue
            try:
                year = int(year_str)
                ref_date = date(year, 1, 1)
                value = Decimal(str(round(float(raw) * scale, 4)))
            except (ValueError, TypeError) as exc:
                log.debug("Skipping WB entry %s/%s: %s", indicator_code, year_str, exc)
                continue
            rows.append({"indicator": indicator_code, "value": value,
                         "reference_date": ref_date, "source": src})
            log.info("%s  %s = %s", indicator_code, year_str, value)

    rows.sort(key=lambda r: (r["indicator"], r["reference_date"]))
    return rows


# ── database ───────────────────────────────────────────────────────────────────
def get_db_conn():
    url = os.environ.get("DATABASE_SYNC_URL", "")
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return psycopg2.connect(url)


UPSERT_MACRO_SQL = """
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
                    cur.execute(UPSERT_MACRO_SQL, row)
                    inserted += 1
    finally:
        conn.close()
    return inserted


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ingest macro indicators (FX rates, policy rate)")
    parser.add_argument(
        "--source",
        choices=["openexchange", "bom", "te", "fluentax", "bom_inflation", "bom_reserves", "wb_macro"],
        default="openexchange",
        help="Data source (default: openexchange — free, no key needed); wb_macro fetches Mongolia CPI+reserves from World Bank",
    )
    parser.add_argument("--discover", action="store_true",
                        help="[bom/bom_inflation/bom_reserves] Save raw HTML and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print rows without writing to DB")
    args = parser.parse_args()

    if args.source == "bom":
        rows = scrape_bom(discover=args.discover)
    elif args.source == "te":
        rows = scrape_trading_economics()
    elif args.source == "fluentax":
        rows = scrape_fluentax()
    elif args.source == "bom_inflation":
        rows = scrape_bom_inflation(discover=args.discover)
    elif args.source == "bom_reserves":
        rows = scrape_bom_reserves(discover=args.discover)
    elif args.source == "wb_macro":
        rows = scrape_wb_macro()
    else:
        rows = scrape_fx_openexchange()

    if args.discover or not rows:
        if not rows and not args.discover:
            log.warning("No macro rows scraped")
        sys.exit(0)

    if args.dry_run:
        for r in rows:
            print(r)
        log.info("Dry run — %d rows found, none inserted", len(rows))
        sys.exit(0)

    inserted = upsert_macro(rows)
    log.info("Upserted %d rows into macro table", inserted)


if __name__ == "__main__":
    main()

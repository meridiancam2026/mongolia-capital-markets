"""
Cbonds web scraper — Mongolia bond prices and yields.

Uses Playwright with the system Chromium (snap) to avoid the
ubuntu26.04-x64 bundled-browser restriction. Set in .env:

    PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/snap/bin/chromium
    CBONDS_USERNAME=cameron.thomas@mu-llc.com
    CBONDS_PASSWORD=Cbonds-Password-2004

Usage:
    python scripts/ingest_cbonds.py --discover-login   # screenshot login page → logs/
    python scripts/ingest_cbonds.py --discover-bonds   # login + screenshot bond page → logs/
    python scripts/ingest_cbonds.py --dry-run          # parse + print rows, no DB write
    python scripts/ingest_cbonds.py                    # full ingest into otc_trades
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

LOGS_DIR = _project_root / "logs"
LOGS_DIR.mkdir(exist_ok=True)

USERNAME = os.environ.get("CBONDS_USERNAME", "")
PASSWORD = os.environ.get("CBONDS_PASSWORD", "")
CHROMIUM_PATH = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "")

CBONDS_LOGIN_URL  = "https://cbonds.com/login/"
SESSION_FILE      = _project_root / "logs" / "cbonds_session.json"

# Mongolia bond listing page candidates — tried in order after login.
# The confirmed working URL (with status/country filters) is first.
MONGOLIA_BOND_URLS = [
    "https://cbonds.com/bonds/?emitent_country_id=3-sg&status_id=5-1z141z4&order=document&dir=asc",
    "https://cbonds.com/bonds/?country=Mongolia",
    "https://cbonds.com/emissions/?country=Mongolia",
    "https://cbonds.com/bonds/mongolia/",
    "https://cbonds.com/country/Mongolia-bond/",
]

UPSERT_SQL = """
INSERT INTO otc_trades (bond_name, price, yield, volume, value, trade_date, market_type)
VALUES (%(bond_name)s, %(price)s, %(yield)s, %(volume)s, %(value)s, %(trade_date)s, %(market_type)s)
ON CONFLICT (bond_name, trade_date) DO UPDATE SET
    price       = EXCLUDED.price,
    yield       = EXCLUDED.yield,
    volume      = EXCLUDED.volume,
    value       = EXCLUDED.value,
    market_type = EXCLUDED.market_type
"""


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def launch_browser(playwright, headless: bool = True):
    """Launch Chromium — prefer system executable (snap) over bundled."""
    kwargs = {
        "headless": headless,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    }
    if CHROMIUM_PATH:
        log.info("Using Chromium at %s", CHROMIUM_PATH)
        kwargs["executable_path"] = CHROMIUM_PATH
    else:
        log.info("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH not set — using bundled Chromium")
    return playwright.chromium.launch(**kwargs)


def new_context(browser, storage_state=None):
    """Create a browser context with realistic viewport + user-agent."""
    kwargs = dict(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        locale="en-US",
    )
    if storage_state:
        kwargs["storage_state"] = storage_state
    return browser.new_context(**kwargs)


def _check_auth(page) -> bool:
    """Read Cbonds' own JS auth flag — most reliable indicator of login state."""
    try:
        user_auth = page.evaluate("() => typeof userAuth !== 'undefined' ? userAuth : -1")
        user_id   = page.evaluate("() => typeof userId   !== 'undefined' ? userId   : -1")
        log.info("Cbonds JS vars: userAuth=%s userId=%s", user_auth, user_id)
        if user_auth == 1 or (isinstance(user_id, (int, float)) and user_id > 0):
            return True
        if user_auth == 0:
            return False
    except Exception as e:
        log.debug("Could not read userAuth JS var: %s", e)
    return None  # unknown


def do_login(page) -> bool:
    """
    Navigate to cbonds.com/login/, fill in credentials, submit.
    Form fields confirmed: name="login" (email), name="password", input[type="submit"].
    Returns True if Cbonds JS userAuth==1 after login.
    """
    log.info("Navigating to %s", CBONDS_LOGIN_URL)
    page.goto(CBONDS_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)

    login_field    = page.locator('input[name="login"]')
    password_field = page.locator('input[name="password"]')

    login_field.wait_for(state="visible", timeout=15_000)
    password_field.wait_for(state="visible", timeout=5_000)

    log.info("Filling credentials for %s", USERNAME)
    login_field.fill(USERNAME)
    password_field.fill(PASSWORD)

    # Use expect_navigation so Playwright waits for the POST redirect
    submit_btn = page.locator('input[type="submit"]')
    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=20_000):
            if submit_btn.count() > 0:
                log.info("Clicking input[type='submit']")
                submit_btn.click()
            else:
                log.info("No submit button — pressing Enter")
                password_field.press("Enter")
    except Exception as e:
        log.debug("Navigation after login submit: %s", e)

    current_url = page.url
    log.info("After login — URL: %s", current_url)

    # Check for visible error messages on the page
    try:
        error_texts = page.locator(
            '[class*="error" i], [class*="invalid" i], [role="alert"]'
        ).all_text_contents()
        for t in error_texts:
            if t.strip():
                log.warning("Page message: %s", t.strip()[:200])
    except Exception:
        pass

    # Primary check: Cbonds JS flag
    auth = _check_auth(page)
    if auth is True:
        log.info("Login confirmed via userAuth==1")
        return True
    if auth is False:
        ss = LOGS_DIR / f"cbonds_login_failed_{_ts()}.png"
        page.screenshot(path=str(ss))
        log.error(
            "Login failed — userAuth==0. "
            "Check credentials or open %s to inspect the page.", ss
        )
        return False

    # Fallback: URL changed away from login
    if "login" not in current_url.lower():
        log.info("Redirected away from login — treating as success")
        return True

    log.warning("Login result unknown — proceeding anyway")
    return True


def _dec(val) -> Decimal | None:
    if val is None:
        return None
    cleaned = re.sub(r"[%\s,]", "", str(val))
    if not cleaned or cleaned in ("-", "—", "N/A", "n/a", ""):
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.0001"))
    except InvalidOperation:
        return None


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y",
                "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            pass
    return None


def _col_index(headers: list[str], *patterns: str) -> int | None:
    pats = [re.compile(p, re.I) for p in patterns]
    for i, h in enumerate(headers):
        for pat in pats:
            if pat.search(h):
                return i
    return None


def parse_tables_from_html(html: str) -> list[dict]:
    """Parse bond rows from HTML tables using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    rows_out = []
    today = date.today()

    tables = soup.find_all("table")
    log.info("Found %d table(s) in page HTML", len(tables))

    for t_idx, table in enumerate(tables):
        header_cells = table.find("tr")
        if not header_cells:
            continue
        raw_headers = [
            th.get_text(separator=" ", strip=True)
            for th in header_cells.find_all(["th", "td"])
        ]
        if len(raw_headers) < 2:
            continue

        log.debug("Table %d headers: %s", t_idx, raw_headers)

        name_col   = _col_index(raw_headers, r"name|bond|emission|isin|ticker|title|issue|security")
        price_col  = _col_index(raw_headers, r"price|last|close|clean|bid|ask|котир")
        yield_col  = _col_index(raw_headers, r"yield|ytm|yld|доходн")
        volume_col = _col_index(raw_headers, r"volume|vol|turnover|qty|объём")
        date_col   = _col_index(raw_headers, r"date|дата|settlement|trade.*date|last.*trade")

        if name_col is None:
            log.debug("Table %d: no name column — skipping", t_idx)
            continue

        log.info(
            "Table %d: name=%s price=%s yield=%s volume=%s date=%s",
            t_idx, name_col, price_col, yield_col, volume_col, date_col,
        )

        data_rows = table.find_all("tr")[1:]
        for row in data_rows:
            cells = row.find_all(["td", "th"])
            if len(cells) <= name_col:
                continue

            def cell(idx: int | None) -> str:
                if idx is None or idx >= len(cells):
                    return ""
                return cells[idx].get_text(separator=" ", strip=True)

            bond_name = cell(name_col)
            if not bond_name or bond_name in ("-", "—"):
                continue

            raw_date  = cell(date_col)
            trade_date = _parse_date(raw_date) or today

            rows_out.append({
                "bond_name":   bond_name[:200],
                "price":       _dec(cell(price_col)),
                "yield":       _dec(cell(yield_col)),
                "volume":      None,
                "value":       None,
                "trade_date":  trade_date,
                "market_type": "cbonds",
            })

    log.info("Parsed %d bond rows from HTML tables", len(rows_out))
    return rows_out


def scrape_via_page_evaluate(page) -> list[dict]:
    """
    Extract bond rows from the Cbonds bond listing table via JS DOM evaluation.
    Table 9 (confirmed) has headers: Issue, ISIN, Indicative price %, Indicative yield %, ...
    Skips calendar tables (Mon/Tue/Wed headers) and column-picker rows.
    """
    today = date.today()
    rows_out = []

    try:
        table_data = page.evaluate("""() => {
            const tables = Array.from(document.querySelectorAll('table'));
            return tables.map(t => {
                const rows = Array.from(t.querySelectorAll('tr'));
                return rows.map(r => {
                    const cells = Array.from(r.querySelectorAll('th,td'));
                    return cells.map(c => (c.innerText || '').trim());
                });
            });
        }""")
    except Exception as e:
        log.warning("JS table evaluation failed: %s", e)
        return []

    for t_idx, table in enumerate(table_data):
        if not table or len(table) < 2:
            continue
        headers = table[0]

        # Skip calendar tables (Mon/Tue/Wed) and empty-header tables
        if not headers or headers[0] in ("Mon", ""):
            continue
        # Skip tables with fewer than 3 data rows (column-picker headers, UI widgets)
        if len(table) < 4:
            continue
        # Skip tables where most headers are "Hide" (column picker)
        hide_count = sum(1 for h in headers if h == "Hide")
        if hide_count > len(headers) / 2:
            continue

        log.debug("JS table %d headers (first 6): %s", t_idx, headers[:6])

        # Column detection — Cbonds confirmed header names
        name_col  = _col_index(headers,
                        r"^issue$|^bond$|^emission$|^name$|^security$",
                        r"issue|bond name")
        if name_col is None:
            # Fallback: first non-ISIN text column
            name_col = _col_index(headers, r"issue|name|bond|security|emission|ticker|title")
        price_col = _col_index(headers, r"indicative price|price")
        yield_col = _col_index(headers, r"indicative yield|yield|ytm")
        isin_col  = _col_index(headers, r"^isin$|isin")
        mat_col   = _col_index(headers, r"^maturity$|maturity date")

        if name_col is None:
            log.debug("Table %d: no name column — skipping", t_idx)
            continue

        log.info(
            "Scraping table %d (%d data rows): name=%d price=%s yield=%s isin=%s",
            t_idx, len(table) - 1, name_col, price_col, yield_col, isin_col,
        )

        for row in table[1:]:
            if len(row) <= name_col:
                continue

            def gcell(idx):
                return row[idx].strip() if idx is not None and idx < len(row) else ""

            bond_name = gcell(name_col)
            if not bond_name or bond_name in ("-", "—", "Hide", "Issue"):
                continue

            # Use ISIN as part of name if available and name is too short
            isin = gcell(isin_col)
            if len(bond_name) < 3 and isin:
                bond_name = isin

            mat_raw    = gcell(mat_col)
            trade_date = _parse_date(mat_raw) or today
            # trade_date for otc_trades = today (maturity is a bond attribute, not trade date)
            trade_date = today

            rows_out.append({
                "bond_name":   bond_name[:200],
                "price":       _dec(gcell(price_col)),
                "yield":       _dec(gcell(yield_col)),
                "volume":      None,
                "value":       None,
                "trade_date":  today,
                "market_type": "cbonds",
            })

    log.info("Extracted %d bond rows via JS DOM", len(rows_out))
    return rows_out


def fetch_bond_page(page) -> str | None:
    """
    Try Mongolia bond URL candidates after login.
    Waits for the Cbonds app-table-2-0 component to appear (JS-rendered).
    Returns the URL that worked, or None.
    """
    for url in MONGOLIA_BOND_URLS:
        log.info("Trying bond URL: %s", url)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            if not resp or resp.status != 200:
                log.debug("  %s → HTTP %s", url, resp.status if resp else "no response")
                continue

            # Wait up to 20s for the bond data table specifically
            # (calendar tables appear first; wait for a th containing "Issue" or "price")
            try:
                page.wait_for_selector(
                    "th:has-text('Issue'), th:has-text('Indicative price'), "
                    "th:has-text('price'), th:has-text('yield')",
                    timeout=20_000,
                )
                log.info("Bond table header appeared at %s", page.url)
            except Exception:
                log.debug("  Bond table header not found within 20s at %s", url)

            n_tables = len(page.query_selector_all("table"))
            log.info("Bond page: %s — %d table(s) found", page.url, n_tables)
            return page.url

        except Exception as e:
            log.debug("  %s → error: %s", url, e)

    return None


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


def setup_session(playwright):
    """
    Open a visible browser window so the user can log in manually (including
    any 2FA / authentication code steps). Saves the resulting session cookies
    to SESSION_FILE so all future headless runs skip the login step.
    """
    log.info("Opening visible browser — log in to Cbonds manually, then close the window.")
    log.info("Session will be saved to: %s", SESSION_FILE)

    browser = launch_browser(playwright, headless=False)
    context = new_context(browser)
    page = context.new_page()

    page.goto(CBONDS_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
    print("\n" + "=" * 60)
    print("  A browser window has opened.")
    print("  1. Log in to cbonds.com (enter your credentials).")
    print("  2. Complete any email/SMS verification code step.")
    print("  3. Once you see your account dashboard, CLOSE the browser window.")
    print("=" * 60 + "\n")

    # Block until the user closes the browser
    try:
        browser.contexts  # keeps reference alive
        page.wait_for_event("close", timeout=300_000)  # 5-minute window
    except Exception:
        pass

    # Save session before browser fully closes
    try:
        context.storage_state(path=str(SESSION_FILE))
        log.info("Session saved → %s", SESSION_FILE)
        print(f"\nSession saved to {SESSION_FILE}")
        print("You can now run:  python scripts/ingest_cbonds.py --discover-bonds")
    except Exception as e:
        log.error("Failed to save session: %s", e)
    finally:
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Cbonds Playwright scraper for Mongolia bonds")
    parser.add_argument("--setup-session", action="store_true",
                        help="Open visible browser so you can log in + complete 2FA, then save cookies")
    parser.add_argument("--discover-login", action="store_true",
                        help="Screenshot login page, print form fields, and exit")
    parser.add_argument("--discover-bonds", action="store_true",
                        help="Login then screenshot bond listing page and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and print rows but do not write to DB")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed. Run: pip install playwright")
        sys.exit(1)

    # ── Setup session (one-time, interactive) ─────────────────────────────
    with sync_playwright() as p:
        if args.setup_session:
            setup_session(p)
            sys.exit(0)

        # Determine auth method: saved session file takes priority over form login
        storage_state = None
        if SESSION_FILE.exists():
            log.info("Loading saved session from %s", SESSION_FILE)
            storage_state = str(SESSION_FILE)
        else:
            if not USERNAME or not PASSWORD:
                log.error(
                    "No saved session found and CBONDS_USERNAME/CBONDS_PASSWORD not set.\n"
                    "Run:  python scripts/ingest_cbonds.py --setup-session"
                )
                sys.exit(1)

        browser = launch_browser(p)
        context = new_context(browser, storage_state=storage_state)
        page = context.new_page()

        # ── Discover login page ──────────────────────────────────────────
        if args.discover_login:
            log.info("Navigating to %s", CBONDS_LOGIN_URL)
            page.goto(CBONDS_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
            page.locator('input[name="login"]').wait_for(state="visible", timeout=15_000)

            ss_path = LOGS_DIR / f"cbonds_login_{_ts()}.png"
            page.screenshot(path=str(ss_path), full_page=True)
            log.info("Screenshot saved → %s", ss_path)

            inputs = page.evaluate("""() =>
                Array.from(document.querySelectorAll('input')).map(i => ({
                    type: i.type, name: i.name, id: i.id,
                    placeholder: i.placeholder, autocomplete: i.autocomplete
                }))
            """)
            print("\n=== Input fields on login page ===")
            for inp in inputs:
                print(f"  {inp}")

            buttons = page.evaluate("""() =>
                Array.from(document.querySelectorAll('button,input[type=submit]'))
                    .map(b => ({ type: b.type, text: (b.innerText || b.value || '').trim().substring(0, 60), id: b.id }))
            """)
            print("\n=== Buttons on login page ===")
            for btn in buttons:
                print(f"  {btn}")

            browser.close()
            sys.exit(0)

        # ── Authenticate (form login if no saved session) ────────────────
        if not storage_state:
            ok = do_login(page)
            if not ok:
                ss_path = LOGS_DIR / f"cbonds_login_failed_{_ts()}.png"
                page.screenshot(path=str(ss_path))
                log.error(
                    "Automated login failed.\n"
                    "If Cbonds requires an authentication/verification code,\n"
                    "run:  python scripts/ingest_cbonds.py --setup-session\n"
                    "to log in manually in a visible browser window."
                )
                browser.close()
                sys.exit(1)
        else:
            # Verify the loaded session is still valid
            page.goto("https://cbonds.com/", wait_until="domcontentloaded", timeout=20_000)
            auth = _check_auth(page)
            if auth is False:
                log.warning(
                    "Saved session has expired. "
                    "Run --setup-session to refresh it."
                )
                # Try form login as fallback
                if USERNAME and PASSWORD:
                    log.info("Falling back to form login…")
                    ok = do_login(page)
                    if ok:
                        context.storage_state(path=str(SESSION_FILE))
                        log.info("Session refreshed → %s", SESSION_FILE)
                else:
                    browser.close()
                    sys.exit(1)
            else:
                log.info("Saved session valid (userAuth=%s)", auth)

        # ── Discover bond page ───────────────────────────────────────────
        if args.discover_bonds:
            bond_url = fetch_bond_page(page)
            if bond_url is None:
                log.error("No Mongolia bond page found — tried %d URLs", len(MONGOLIA_BOND_URLS))
                ss_path = LOGS_DIR / f"cbonds_bonds_notfound_{_ts()}.png"
                page.screenshot(path=str(ss_path))
                browser.close()
                sys.exit(1)

            ss_path = LOGS_DIR / f"cbonds_bonds_{_ts()}.png"
            page.screenshot(path=str(ss_path), full_page=True)
            log.info("Screenshot → %s", ss_path)

            html_path = LOGS_DIR / f"cbonds_bonds_{_ts()}.html"
            html_path.write_text(page.content(), encoding="utf-8")
            log.info("HTML → %s", html_path)

            auth = _check_auth(page)
            n_tables = len(page.query_selector_all("table"))
            n_rows   = len(page.query_selector_all("table tr"))
            print(f"\n=== Bond page: {bond_url} ===")
            print(f"  Authenticated: {auth}")
            print(f"  Tables:        {n_tables}")
            print(f"  Total rows:    {n_rows}")

            header_data = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('table')).map((t, i) => ({
                    index: i,
                    headers: Array.from(t.querySelectorAll('th')).map(h => h.innerText.trim()),
                    rows: t.querySelectorAll('tr').length
                }));
            }""")
            for t in header_data:
                print(f"  Table {t['index']}: {t['rows']} rows, headers={t['headers']}")

            browser.close()
            sys.exit(0)

        # ── Full ingest ──────────────────────────────────────────────────
        bond_url = fetch_bond_page(page)
        if bond_url is None:
            log.error(
                "No Mongolia bond page found. "
                "Run --discover-bonds to inspect which URLs are accessible."
            )
            browser.close()
            sys.exit(1)

        rows = scrape_via_page_evaluate(page)
        if not rows:
            rows = parse_tables_from_html(page.content())

        browser.close()

    if not rows:
        log.error(
            "No bond data extracted. "
            "Run --discover-bonds to inspect page structure."
        )
        sys.exit(1)

    if args.dry_run:
        for r in rows:
            print(r)
        log.info("Dry run — %d rows parsed, none inserted", len(rows))
        return

    n = upsert(rows)
    log.info("Done — %d bond rows upserted into otc_trades (market_type=cbonds)", n)


if __name__ == "__main__":
    main()

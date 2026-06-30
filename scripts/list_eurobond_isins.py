"""Print ISIN + currency for all non-MNT Mongolia bonds from Cbonds API."""
import json
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SESSION_FILE = PROJECT / "logs" / "cbonds_session.json"

storage = json.load(open(SESSION_FILE))
cookie_header = "; ".join(
    f"{c['name']}={c['value']}"
    for c in storage.get("cookies", [])
    if "cbonds.com" in c.get("domain", "")
)

body = {
    "filters": [
        {"field": "show_global", "operator": "eq", "value": 1},
        {"field": "emitent_country_id", "operator": "in", "value": ["106"]},
    ],
    "sorting": [{"field": "document", "order": "asc"}],
    "quantity": {"offset": 0, "limit": 500, "page": 1},
    "lang": "eng",
    "expand_rel_fields": [
        "emitent_country", "status_id", "emitent_branch_id",
        "emitent_type", "coupon_type_id", "kind_id", "subkind_id", "bond_rank",
    ],
    "fromPreConfig": False,
}

req = urllib.request.Request(
    "https://cbonds.com/api/bonds/search/",
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie_header,
        "Origin": "https://cbonds.com",
        "Referer": "https://cbonds.com/bonds/",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    },
    method="POST",
)

data = json.loads(urllib.request.urlopen(req, timeout=30).read())
print(f"Top-level keys: {list(data.keys())}")
resp = data.get("response", {})
if isinstance(resp, dict):
    print(f"response keys: {list(resp.keys())}")
    print(f"response.total: {resp.get('total')}")
items = (resp.get("data") or resp.get("items") or []) if isinstance(resp, dict) else []

print(f"Total bonds returned: {len(items)}")
if items:
    first = items[0]
    # Show all keys that contain "curr", "isin", "currency", "ccy"
    relevant = {k: v for k, v in first.items()
                if any(x in k.lower() for x in ("curr", "isin", "ccy", "document", "id"))}
    print(f"First bond relevant fields: {relevant}")
    print()

print(f"{'BOND NAME':<62} {'ISIN':<16} CCY")
print("-" * 85)
for b in items:
    ccy = b.get("currency_name", "")
    if ccy and ccy != "MNT":
        name = (b.get("document") or "").strip()[:60]
        isin = (b.get("isin_code") or "").strip()
        print(f"{name:<62} {isin:<16} {ccy}")

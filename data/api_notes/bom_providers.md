# BOM Data Providers — Comparison & Setup Notes

The Bank of Mongolia has no public API. Three options exist for retrieving
MNT exchange rates, the policy rate, and inflation data.

---

## Option A — Fluentax (Recommended for FX)

**What it provides:** MNT exchange rates sourced from BOM, updated daily.

**Registration:** https://fluentax.mn
- Sign up for a free account to obtain an API key.
- Check whether the MNT FX endpoint is accessible on the free tier before committing to a paid plan.

**Expected endpoint structure (verify in their docs after signup):**
```
GET https://api.fluentax.mn/v1/rates?base=MNT&date=2026-06-24
Authorization: Bearer <FLUENTAX_API_KEY>
```

**Expected response fields:**
```json
{
  "base": "MNT",
  "date": "2026-06-24",
  "rates": {
    "USD": 0.000285,
    "EUR": 0.000262,
    "CNY": 0.00207,
    "JPY": 0.0435
  }
}
```

**Storing the key:** Add to `.env` as `FLUENTAX_API_KEY=your_key_here`

**Recommendation:** Use Fluentax as the primary FX source — it is Mongolia-specific
and sources directly from BOM, giving better accuracy for MNT pairs than global providers.

---

## Option B — Trading Economics (Recommended for Policy Rate & Inflation)

**What it provides:** 20M+ economic indicators including BOM policy rate, inflation,
GDP, and FX series for Mongolia.

**Registration:** https://tradingeconomics.com/api
- A free trial key is available; check call limits before production use.
- Paid plans start at ~$25/month for the API tier.

**Key series identifiers for Mongolia:**
| Series | TE Indicator ID | Notes |
|--------|----------------|-------|
| Policy rate | `MN:INTERESTRATE` | BOM benchmark rate (12% as of 2026) |
| Inflation (CPI YoY) | `MN:INFLATIONRATE` | Monthly |
| USD/MNT | `USDMNT` | Daily FX rate |
| GDP growth | `MN:GDPANNUALGROWTHRATE` | Quarterly |

**Example API call (after obtaining key):**
```python
import requests
url = "https://api.tradingeconomics.com/indicator/MN:INTERESTRATE"
params = {"c": "your_api_key:your_api_key"}
response = requests.get(url, params=params)
data = response.json()
# Returns: [{"Country": "Mongolia", "Category": "Interest Rate",
#            "LastUpdate": "...", "Value": 12.0, ...}]
```

**Storing the key:** Add to `.env` as `TRADING_ECONOMICS_API_KEY=your_key_here`

**Recommendation:** Use Trading Economics for the policy rate and inflation series,
since these are low-frequency (updated monthly/per meeting) and TE's coverage is reliable.

---

## Option C — Direct BOM Scrape (Fallback)

**URL:** https://www.mongolbank.mn/en/p/exchangerates

**Method:** `requests` + `BeautifulSoup` to parse the daily FX table.

**Pros:** Free, no API key, data straight from source.
**Cons:** Fragile — HTML structure can change; no guarantee of uptime; no historical series.

**When to use:** Only if both Fluentax and Trading Economics are unavailable or too costly.
Implementation template in `scripts/ingest_bom_scrape.py` (Stage 4).

---

## Recommended Setup

| Data | Provider | Frequency |
|------|----------|-----------|
| MNT/USD, MNT/EUR, MNT/CNY | Fluentax | Daily |
| BOM policy rate | Trading Economics | Weekly (or per MPC meeting) |
| Inflation (CPI) | Trading Economics | Monthly |

**Action items:**
1. Register at https://fluentax.mn → add `FLUENTAX_API_KEY` to `.env`
2. Register at https://tradingeconomics.com/api → add `TRADING_ECONOMICS_API_KEY` to `.env`
3. Test both with a single API call before Stage 4 ingestion scripts are written
4. Update `DATA_SOURCES.md` status for BOM (§3), Trading Economics (§6), and Fluentax (§7)

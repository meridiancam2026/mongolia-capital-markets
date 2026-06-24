# Data Sources — Licensing & Access Status

Update the **Status** column as outreach progresses. Valid values:
`pending` | `requested` | `approved` | `scraping-permitted` | `api-key-obtained` | `no-response` | `denied`

---

## 1. Mongolian Stock Exchange (MSE) — Listed Equities

| Field | Value |
|-------|-------|
| **Data type** | Real-time equity quotes (OHLCV, bid/ask, volume, value) |
| **Coverage** | ~161 listed securities |
| **Update frequency** | Live during trading hours (09:00–17:00 UBT, Mon–Fri) |
| **Public URL** | https://mse.mn/mn/markets/todaytrade |
| **Contact** | info@mse.mn (general) — identify IT/market-ops dept on website |
| **Status** | `pending` |
| **Outreach date** | — |
| **Response date** | — |
| **Notes** | Metricon provides a licensed API (see §5). Email template: `data/email_templates/mse_outreach.md` |

---

## 2. MASD / OTC.mn — OTC Bond Market

| Field | Value |
|-------|-------|
| **Data type** | Daily OTC bond trades (price, yield, volume, market type) |
| **Coverage** | Corporate and government bonds registered on M-OTC |
| **Update frequency** | Daily, after market close |
| **Public URL** | https://masd.mn/otc/market-data |
| **Operator** | AND Systems LLC (OTC.mn platform operator) |
| **Contact** | Via https://masd.mn/contact or info@masd.mn |
| **Status** | `pending` |
| **Outreach date** | — |
| **Response date** | — |
| **Notes** | Email template: `data/email_templates/masd_outreach.md` |

---

## 3. Bank of Mongolia (BOM) — FX Rates & Policy Rate

| Field | Value |
|-------|-------|
| **Data type** | Daily MNT exchange rates (USD, EUR, CNY, JPY, etc.), benchmark policy rate, inflation |
| **Update frequency** | FX: daily. Policy rate: per MPC meeting (~6× per year) |
| **Public URL** | https://www.mongolbank.mn/en/p/exchangerates |
| **Official API** | None (no public API) |
| **Third-party option A** | Fluentax — see `data/api_notes/bom_providers.md` |
| **Third-party option B** | Trading Economics — see `data/api_notes/bom_providers.md` |
| **Status** | `pending` — choose provider and obtain API key |
| **Notes** | Registration URLs in `data/api_notes/bom_providers.md`. No outreach email needed; use third-party API or scrape. |

---

## 4. Financial Regulatory Commission (FRC) — Regulatory Statistics

| Field | Value |
|-------|-------|
| **Data type** | Annual capital-market statistics (market cap, OTC registered debt, number of issuers) |
| **Update frequency** | Annual (published in FRC Annual Report, usually Q1 following year) |
| **Public URL** | https://www.frc.mn/en (Annual Reports section) |
| **Official API** | None (PDF reports only) |
| **Status** | `scraping-permitted` — public annual reports, manually extracted |
| **Seed file** | `data/frc_stats.csv` |
| **Notes** | Known values: capital-market value MNT 11.6 trillion; OTC registered debt MNT 2,441.4 billion (reference year 2023). Update annually. |

---

## 5. Metricon — MSE Data API (Third-Party)

| Field | Value |
|-------|-------|
| **Data type** | Real-time MSE prices, OHLCV history (12+ years), fundamentals, dividends, signals |
| **Coverage** | 161 MSE-listed stocks |
| **Planned API endpoints** | `GET /stocks`, `GET /ohlcv/{ticker}`, `GET /fundamentals/{ticker}`, `GET /dividends/{ticker}`, `GET /signal/{ticker}`, WebSocket `/live` (5s cadence) |
| **Registration** | See `data/api_notes/metricon.md` |
| **Status** | `pending` — API not yet publicly available; sign up to waitlist |
| **Notes** | When available, replaces MSE scraper in Stage 3. |

---

## 6. Trading Economics — Macro Data API

| Field | Value |
|-------|-------|
| **Data type** | 20M+ economic indicators including BOM policy rate, inflation, FX series |
| **Relevant series** | `MN:INTERESTRATE` (policy rate), `USDMNT` (FX), `MN:INFLATIONRATE` |
| **Registration** | https://tradingeconomics.com/api |
| **Free tier** | Limited calls; sufficient for daily macro updates |
| **Status** | `pending` — register for trial key |
| **Notes** | Details in `data/api_notes/bom_providers.md` |

---

## 7. Fluentax — BOM FX API

| Field | Value |
|-------|-------|
| **Data type** | MNT exchange rates sourced directly from BOM |
| **Relevant endpoint** | `/currency/rates?base=MNT` (structure TBC) |
| **Registration** | https://fluentax.mn |
| **Status** | `pending` — register and test endpoint |
| **Notes** | Mongolia-specific provider; may have better MNT coverage than Trading Economics. Details in `data/api_notes/bom_providers.md` |

---

## Status Summary

| Source | Category | Status | Priority |
|--------|----------|--------|----------|
| MSE | Equities | `pending` | High — needed for Stage 3 |
| MASD / OTC.mn | Bonds | `pending` | High — needed for Stage 4 |
| BOM (via Fluentax or TE) | Macro | `pending` | Medium — needed for Stage 4 |
| FRC | Regulatory | `scraping-permitted` | Low — annual seed data only |
| Metricon | Equities (future) | `pending` | Medium — replaces scraper when live |
| Trading Economics | Macro | `pending` | Medium — fallback for BOM data |
| Fluentax | Macro (FX) | `pending` | Medium — primary BOM FX source |

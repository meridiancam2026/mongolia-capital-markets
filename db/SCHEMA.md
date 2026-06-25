# Database Schema

PostgreSQL 18.4. Six application tables + `alembic_version` (Alembic internal).
All timestamps are `TIMESTAMPTZ` (UTC). Monetary values are `NUMERIC` (arbitrary precision).

> **TimescaleDB note**: Hypertable conversion of `quotes` (partitioned by `trade_time`) is
> deferred — no package available for Ubuntu 26.04 + PostgreSQL 18 as of 2026-06-25.
> When a compatible release ships, run `SELECT create_hypertable('quotes', 'trade_time')`.

---

## securities

Ticker registry. One row per MSE-listed equity. Populated by `db/seed.py` (static) and
upserted on every `scripts/ingest_mse.py` run.

| Column    | Type        | Nullable | Notes                    |
|-----------|-------------|----------|--------------------------|
| ticker    | TEXT        | NOT NULL | Primary key              |
| full_name | TEXT        |          |                          |
| sector    | TEXT        |          |                          |
| created_at| TIMESTAMPTZ | NOT NULL | Default: now()           |

**Constraints**: `PRIMARY KEY (ticker)`

---

## quotes

Intraday MSE equity price snapshots. One row per ticker per scraper run.

| Column      | Type        | Nullable | Notes                             |
|-------------|-------------|----------|-----------------------------------|
| id          | BIGSERIAL   | NOT NULL | Primary key                       |
| ticker      | TEXT        | NOT NULL | FK → securities(ticker)           |
| trade_time  | TIMESTAMPTZ | NOT NULL | Timestamp of the price snapshot   |
| open        | NUMERIC     |          |                                   |
| high        | NUMERIC     |          |                                   |
| low         | NUMERIC     |          |                                   |
| close       | NUMERIC     |          |                                   |
| prev_close  | NUMERIC     |          |                                   |
| last        | NUMERIC     |          |                                   |
| change      | NUMERIC     |          | Absolute change from prev_close   |
| change_pct  | NUMERIC     |          | Percentage change                 |
| volume      | BIGINT      |          | Shares traded                     |
| value       | NUMERIC     |          | MNT value traded                  |
| bid_price   | NUMERIC     |          |                                   |
| bid_qty     | BIGINT      |          |                                   |
| ask_price   | NUMERIC     |          |                                   |
| ask_qty     | BIGINT      |          |                                   |

**Indexes**:
- `idx_quotes_ticker` on `(ticker)`
- `idx_quotes_trade_time` on `(trade_time DESC)`

---

## otc_trades

MASD M-OTC bond market leaderboard. Top-5 most-active bonds per day by total MNT value.
Individual per-transaction data (price, yield) requires authenticated OTC.mn access.

| Column      | Type        | Nullable | Notes                             |
|-------------|-------------|----------|-----------------------------------|
| id          | BIGSERIAL   | NOT NULL | Primary key                       |
| bond_name   | TEXT        | NOT NULL |                                   |
| trade_date  | DATE        | NOT NULL |                                   |
| price       | NUMERIC     |          | NULL — not available on public page |
| yield       | NUMERIC     |          | NULL — not available on public page |
| volume      | BIGINT      |          | NULL — not available on public page |
| value       | NUMERIC     |          | Total MNT value for the day       |
| market_type | TEXT        |          |                                   |

**Constraints**: `UNIQUE (bond_name, trade_date)`

**Indexes**: `idx_otc_trades_date` on `(trade_date DESC)`

---

## macro

Time-series of macroeconomic indicators. Sources: MASD (market aggregates) and
open.er-api.com (FX rates). Policy rate is seeded manually from FRC CSV.

| Column         | Type        | Nullable | Notes                           |
|----------------|-------------|----------|---------------------------------|
| id             | BIGSERIAL   | NOT NULL | Primary key                     |
| indicator      | TEXT        | NOT NULL | Indicator code (see below)      |
| value          | NUMERIC     | NOT NULL |                                 |
| reference_date | DATE        | NOT NULL | Date the value applies to       |
| source         | TEXT        |          | "MASD", "open.er-api.com", etc. |
| fetched_at     | TIMESTAMPTZ | NOT NULL | Default: now()                  |

**Constraints**: `UNIQUE (indicator, reference_date)`

**Indexes**: `idx_macro_indicator` on `(indicator)`

**Indicator codes**:

| Code                      | Description                        | Source          |
|---------------------------|------------------------------------|-----------------|
| FX_USD_MNT                | USD/MNT exchange rate              | open.er-api.com |
| FX_EUR_MNT                | EUR/MNT exchange rate              | open.er-api.com |
| FX_CNY_MNT                | CNY/MNT exchange rate              | open.er-api.com |
| FX_RUB_MNT                | RUB/MNT exchange rate              | open.er-api.com |
| FX_JPY_MNT                | JPY/MNT exchange rate              | open.er-api.com |
| FX_KRW_MNT                | KRW/MNT exchange rate              | open.er-api.com |
| FX_GBP_MNT                | GBP/MNT exchange rate              | open.er-api.com |
| MASD_SECONDARY_MARKET_MNT | MASD secondary market daily total  | MASD            |
| MASD_PRIMARY_MARKET_MNT   | MASD primary market daily total    | MASD            |
| MASD_OTC_BOND_BALANCE_MNT | Total outstanding OTC bond balance | MASD            |

---

## regulatory_stats

Annual figures from the Financial Regulatory Commission (FRC). Updated ~annually.
Seeded from `data/frc_stats.csv` via `scripts/seed_frc_stats.py`.

| Column         | Type    | Nullable | Notes                           |
|----------------|---------|----------|---------------------------------|
| id             | SERIAL  | NOT NULL | Primary key                     |
| indicator      | TEXT    | NOT NULL | Indicator code (see below)      |
| value          | NUMERIC | NOT NULL |                                 |
| reference_year | INTEGER | NOT NULL |                                 |
| source         | TEXT    |          | "FRC"                           |

**Constraints**: `UNIQUE (indicator, reference_year)`

**Indicator codes**:

| Code                 | Description                              | Unit |
|----------------------|------------------------------------------|------|
| capital_market_value | Total capital market value               | MNT  |
| otc_registered_debt  | Total OTC registered debt                | MNT  |
| listed_companies     | Number of MSE-listed companies           | count|
| policy_rate          | BOM monetary policy rate at year-end     | %    |

---

## news

News articles scraped from MSE/MASD/FRC news feeds (Stage 6+, not yet populated).

| Column      | Type        | Nullable | Notes                       |
|-------------|-------------|----------|-----------------------------|
| id          | SERIAL      | NOT NULL | Primary key                 |
| title       | TEXT        | NOT NULL |                             |
| summary     | TEXT        |          |                             |
| source_url  | TEXT        |          | Unique                      |
| published_at| TIMESTAMPTZ |          |                             |

**Indexes**: `idx_news_published_at` on `(published_at DESC)`

---

## Migration chain

```
001_create_initial_tables.py   → securities, quotes
002_add_quotes_indexes.py      → idx_quotes_ticker, idx_quotes_trade_time
003_create_otc_macro_tables.py → otc_trades, macro, regulatory_stats
004_create_news_table.py       → news, idx_news_published_at
```

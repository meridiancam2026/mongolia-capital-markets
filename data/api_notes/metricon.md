# Metricon — MSE Data API Notes

Metricon is a Mongolian fintech platform that provides licensed real-time and
historical MSE data. Its API is the preferred long-term replacement for the
MSE scraper built in Stage 3.

---

## Current Status (as of 2026-06)

- The Metricon platform is live at https://metricon.mn (verify current URL)
- Real-time prices for 161 MSE-listed stocks are available on the platform
- **API status**: Upcoming / in development — not yet publicly available
- Sign up for the waitlist / early access on their website

---

## Planned API Endpoints

Once available, the Metricon API is expected to expose:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stocks` | GET | List of all MSE-listed securities with metadata |
| `/ohlcv/{ticker}` | GET | Historical OHLCV data for a ticker |
| `/fundamentals/{ticker}` | GET | P/E, EPS, book value, market cap, etc. |
| `/dividends/{ticker}` | GET | Dividend history |
| `/signal/{ticker}` | GET | Multi-indicator technical signal score |
| `/live` | WebSocket | Real-time tick stream at 5-second cadence |

---

## Example Usage (when API is live)

**REST — latest OHLCV:**
```python
import requests
url = "https://api.metricon.mn/ohlcv/MIE"   # example ticker
headers = {"Authorization": f"Bearer {METRICON_API_KEY}"}
params = {"from": "2026-01-01", "to": "2026-06-24", "interval": "1d"}
response = requests.get(url, headers=headers)
candles = response.json()
```

**WebSocket — live tick stream:**
```python
import asyncio, websockets, json

async def stream_quotes():
    uri = "wss://api.metricon.mn/live"
    headers = {"Authorization": f"Bearer {METRICON_API_KEY}"}
    async with websockets.connect(uri, extra_headers=headers) as ws:
        async for message in ws:
            tick = json.loads(message)
            # tick: {"ticker": "MIE", "last": 1250.0, "volume": 450, "time": "..."}
            await process_tick(tick)
```

---

## How Metricon Replaces the Stage 3 Scraper

When the Metricon API is live:
1. Update `scripts/ingest_metricon.py` (stubbed in Stage 3) with real credentials.
2. Use `GET /ohlcv/{ticker}` for historical backfill.
3. Subscribe to WebSocket `/live` for real-time ticks → write to Redis → flush to `quotes` table.
4. Disable or remove `scripts/ingest_mse.py` (the Playwright scraper).
5. Add `GET /fundamentals/{ticker}` data to the Stock Detail page in Stage 7.

---

## Action Items

1. Visit https://metricon.mn and create an account.
2. Check if API documentation is publicly available.
3. If an early-access / waitlist form exists, submit it.
4. Add your `METRICON_API_KEY` to `.env` once received (currently set to `placeholder`).
5. Update `DATA_SOURCES.md` status for Metricon (§5) once signed up.

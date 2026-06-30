import asyncio
import logging
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated, Optional

import httpx
import psycopg2
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import EquityPriceHistory, Quote, Security
from backend.schemas import EquityHistoryOut, QuoteOut

router = APIRouter()
log = logging.getLogger(__name__)

_LATEST_SQL = text("""
    SELECT DISTINCT ON (ticker)
        id, ticker, trade_time, open, high, low, last, prev_close,
        close, change, change_pct, volume, value,
        bid_price, bid_qty, ask_price, ask_qty
    FROM quotes
    ORDER BY ticker, trade_time DESC
""")

_UPSERT_QUOTE = """
INSERT INTO quotes (
    ticker, trade_time, open, high, low, last, prev_close, close, change, change_pct,
    volume, value, bid_qty, bid_price, ask_qty, ask_price
) VALUES (
    %(ticker)s, %(trade_time)s, %(open)s, %(high)s, %(low)s, %(last)s,
    %(prev_close)s, %(close)s, %(change)s, %(change_pct)s, %(volume)s, %(value)s,
    %(bid_qty)s, %(bid_price)s, %(ask_qty)s, %(ask_price)s
)
ON CONFLICT (ticker, trade_time) DO UPDATE SET
    last=EXCLUDED.last, close=EXCLUDED.close, high=EXCLUDED.high, low=EXCLUDED.low,
    change=EXCLUDED.change, change_pct=EXCLUDED.change_pct,
    volume=EXCLUDED.volume, value=EXCLUDED.value,
    bid_qty=EXCLUDED.bid_qty, bid_price=EXCLUDED.bid_price,
    ask_qty=EXCLUDED.ask_qty, ask_price=EXCLUDED.ask_price
"""

_UPSERT_HISTORY = """
INSERT INTO equity_price_history
    (ticker, trade_date, open, high, low, close, change, change_pct, volume, value)
VALUES
    (%(ticker)s, %(trade_date)s, %(open)s, %(high)s, %(low)s, %(close)s,
     %(change)s, %(change_pct)s, %(volume)s, %(value)s)
ON CONFLICT (ticker, trade_date) DO UPDATE SET
    open=COALESCE(EXCLUDED.open, equity_price_history.open),
    high=COALESCE(EXCLUDED.high, equity_price_history.high),
    low=COALESCE(EXCLUDED.low, equity_price_history.low),
    close=COALESCE(EXCLUDED.close, equity_price_history.close),
    change=COALESCE(EXCLUDED.change, equity_price_history.change),
    change_pct=COALESCE(EXCLUDED.change_pct, equity_price_history.change_pct),
    volume=COALESCE(EXCLUDED.volume, equity_price_history.volume),
    value=COALESCE(EXCLUDED.value, equity_price_history.value)
"""

_ENSURE_TICKER = "INSERT INTO securities (ticker) VALUES (%s) ON CONFLICT (ticker) DO NOTHING"


def _dec(text: str) -> Optional[Decimal]:
    cleaned = text.strip().replace(",", "").replace("%", "")
    if not cleaned or cleaned in ("-", "—", "N/A"):
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _int(text: str) -> Optional[int]:
    cleaned = text.strip().replace(",", "")
    if not cleaned or cleaned in ("-", "—"):
        return None
    try:
        return int(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


async def _fetch_mse_rows() -> list[dict]:
    """Fetch MSE today's-trade via plain HTTP — page is SSR, no browser needed."""
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(
            "https://mse.mn/todays-trade",
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"},
        )
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    now = datetime.now(timezone.utc)
    today = date.today()
    rows = []

    for tr in soup.select("table tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if len(cells) < 11:
            continue
        ticker = cells[0].strip().upper()
        if not ticker or ticker in ("TICKER", "СИМБОЛ", "№", "#"):
            continue

        c = cells
        rows.append({
            "ticker":     ticker,
            "open":       _dec(c[1])  if len(c) > 1  else None,
            "high":       _dec(c[2])  if len(c) > 2  else None,
            "low":        _dec(c[3])  if len(c) > 3  else None,
            "last":       _dec(c[4])  if len(c) > 4  else None,
            "prev_close": _dec(c[5])  if len(c) > 5  else None,
            "close":      _dec(c[6])  if len(c) > 6  else None,
            "change":     _dec(c[7])  if len(c) > 7  else None,
            "change_pct": _dec(c[8])  if len(c) > 8  else None,
            "volume":     _int(c[9])  if len(c) > 9  else None,
            "value":      _dec(c[10]) if len(c) > 10 else None,
            "bid_qty":    _int(c[11]) if len(c) > 11 else None,
            "bid_price":  _dec(c[12]) if len(c) > 12 else None,
            "ask_qty":    _int(c[13]) if len(c) > 13 else None,
            "ask_price":  _dec(c[14]) if len(c) > 14 else None,
            "trade_time": now,
            "trade_date": today,
        })

    log.info("MSE httpx scrape: %d rows", len(rows))
    return rows


def _upsert_rows(rows: list[dict]) -> int:
    url = os.environ.get("DATABASE_SYNC_URL") or os.environ.get("DATABASE_URL", "")
    for old, new in [("postgresql+asyncpg://", "postgresql://"),
                     ("postgresql+psycopg2://", "postgresql://"),
                     ("postgres://", "postgresql://")]:
        if url.startswith(old):
            url = url.replace(old, new, 1)
            break
    conn = psycopg2.connect(url)
    count = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(_ENSURE_TICKER, (row["ticker"],))
                    cur.execute(_UPSERT_QUOTE, row)
                    if row.get("close") is not None or row.get("last") is not None:
                        cur.execute(_UPSERT_HISTORY, {**row, "close": row.get("close") or row.get("last")})
                    count += 1
    finally:
        conn.close()
    return count


@router.get("", response_model=list[QuoteOut])
async def list_latest_quotes(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(_LATEST_SQL)
    rows = result.mappings().all()
    return [QuoteOut.model_validate(dict(r)) for r in rows]


@router.post("/refresh", status_code=200)
async def refresh_quotes():
    """Scrape MSE via httpx (no browser) and upsert into quotes + equity_price_history."""
    try:
        rows = await _fetch_mse_rows()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"MSE fetch failed: {e}")

    if not rows:
        raise HTTPException(status_code=503, detail="MSE returned no rows — page structure may have changed")

    count = await asyncio.to_thread(_upsert_rows, rows)
    return {"status": "ok", "rows": count}


@router.get("/{ticker}/history", response_model=list[EquityHistoryOut])
async def get_equity_history(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sec = await db.get(Security, ticker.upper())
    if sec is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker.upper()!r} not found")

    stmt = (
        select(EquityPriceHistory)
        .where(EquityPriceHistory.ticker == ticker.upper())
        .order_by(EquityPriceHistory.trade_date.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{ticker}", response_model=list[QuoteOut])
async def get_ticker_quotes(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    sec = await db.get(Security, ticker.upper())
    if sec is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker.upper()!r} not found")

    stmt = (
        select(Quote)
        .where(Quote.ticker == ticker.upper())
        .order_by(Quote.trade_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

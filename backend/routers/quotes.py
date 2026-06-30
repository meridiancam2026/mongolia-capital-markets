import asyncio
import logging
import sys
from pathlib import Path
from typing import Annotated, Optional

log = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import EquityPriceHistory, Quote, Security
from backend.schemas import EquityHistoryOut, QuoteOut

router = APIRouter()

_LATEST_SQL = text("""
    SELECT DISTINCT ON (ticker)
        id, ticker, trade_time, open, high, low, last, prev_close,
        close, change, change_pct, volume, value,
        bid_price, bid_qty, ask_price, ask_qty
    FROM quotes
    ORDER BY ticker, trade_time DESC
""")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@router.get("", response_model=list[QuoteOut])
async def list_latest_quotes(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(_LATEST_SQL)
    rows = result.mappings().all()
    return [QuoteOut.model_validate(dict(r)) for r in rows]


@router.post("/refresh", status_code=200)
async def refresh_quotes():
    """Trigger an MSE scrape and return when complete (max 60s)."""
    script = _PROJECT_ROOT / "scripts" / "ingest_mse.py"
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(_PROJECT_ROOT),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        stdout_txt = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_txt = stderr.decode("utf-8", errors="replace") if stderr else ""
        log.info("MSE scraper stdout: %s", stdout_txt[-1000:])
        if stderr_txt:
            log.warning("MSE scraper stderr: %s", stderr_txt[-1000:])
        if proc.returncode != 0:
            raise HTTPException(status_code=503, detail=stderr_txt[-800:] or stdout_txt[-800:] or "Scraper exited non-zero")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Scraper timed out after 60s")
    return {"status": "ok"}


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

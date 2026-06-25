from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Quote, Security
from backend.schemas import QuoteOut

router = APIRouter()

_LATEST_SQL = text("""
    SELECT DISTINCT ON (ticker)
        id, ticker, trade_time, open, high, low, last, prev_close,
        close, change, change_pct, volume, value,
        bid_price, bid_qty, ask_price, ask_qty
    FROM quotes
    ORDER BY ticker, trade_time DESC
""")


@router.get("", response_model=list[QuoteOut])
async def list_latest_quotes(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(_LATEST_SQL)
    rows = result.mappings().all()
    return [QuoteOut.model_validate(dict(r)) for r in rows]


@router.get("/{ticker}", response_model=list[QuoteOut])
async def get_ticker_quotes(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    # Verify ticker exists
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

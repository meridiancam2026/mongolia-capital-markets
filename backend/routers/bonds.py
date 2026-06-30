from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import BondPriceHistory
from backend.schemas import BondPriceHistoryOut

router = APIRouter()


@router.get("/history", response_model=list[BondPriceHistoryOut])
async def get_bond_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    bond_name: str = Query(..., description="Exact bond name to look up history for"),
):
    stmt = (
        select(BondPriceHistory)
        .where(BondPriceHistory.bond_name == bond_name)
        .order_by(BondPriceHistory.trade_date)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import OtcTrade
from backend.schemas import OtcTradeOut

router = APIRouter()


@router.get("", response_model=list[OtcTradeOut])
async def list_otc(db: Annotated[AsyncSession, Depends(get_db)]):
    max_date = select(func.max(OtcTrade.trade_date)).scalar_subquery()
    stmt = (
        select(OtcTrade)
        .where(OtcTrade.trade_date == max_date)
        .order_by(OtcTrade.value.desc().nulls_last())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

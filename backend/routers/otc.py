from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import OtcTrade
from backend.schemas import OtcBondRegistryOut, OtcTradeOut

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


@router.get("/registry", response_model=list[OtcBondRegistryOut])
async def list_bond_registry(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        text("SELECT * FROM otc_bond_registry ORDER BY board_category, bond_name")
    )
    return [OtcBondRegistryOut.model_validate(dict(r)) for r in result.mappings().all()]

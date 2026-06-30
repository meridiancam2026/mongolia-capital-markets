from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import OtcTrade
from backend.schemas import OtcBondRegistryOut, OtcTradeOut

router = APIRouter()


@router.get("", response_model=list[OtcTradeOut])
async def list_otc(
    db: Annotated[AsyncSession, Depends(get_db)],
    segment: Optional[Literal["local", "eurobond"]] = Query(None),
):
    max_date = select(func.max(OtcTrade.trade_date)).scalar_subquery()
    stmt = select(OtcTrade).where(OtcTrade.trade_date == max_date)

    if segment == "local":
        stmt = stmt.where(OtcTrade.currency == "MNT")
    elif segment == "eurobond":
        stmt = stmt.where(OtcTrade.currency != "MNT")

    stmt = stmt.order_by(OtcTrade.value.desc().nulls_last())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/registry", response_model=list[OtcBondRegistryOut])
async def list_bond_registry(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        text("SELECT * FROM otc_bond_registry ORDER BY board_category, bond_name")
    )
    return [OtcBondRegistryOut.model_validate(dict(r)) for r in result.mappings().all()]

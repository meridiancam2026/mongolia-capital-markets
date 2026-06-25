from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import RegulatoryStats
from backend.schemas import RegulatoryStatOut

router = APIRouter()


@router.get("", response_model=list[RegulatoryStatOut])
async def list_regulatory(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(RegulatoryStats).order_by(
        RegulatoryStats.reference_year.desc(), RegulatoryStats.indicator
    )
    result = await db.execute(stmt)
    return result.scalars().all()

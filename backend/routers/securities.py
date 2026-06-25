from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Security
from backend.schemas import SecurityOut

router = APIRouter()


@router.get("", response_model=list[SecurityOut])
async def list_securities(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Security).order_by(Security.ticker))
    return result.scalars().all()

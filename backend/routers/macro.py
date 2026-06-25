from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import MacroOut

router = APIRouter()

_LATEST_ALL_SQL = text("""
    SELECT DISTINCT ON (indicator) id, indicator, value, reference_date, source
    FROM macro
    ORDER BY indicator, reference_date DESC
""")

_LATEST_FX_SQL = text("""
    SELECT DISTINCT ON (indicator) id, indicator, value, reference_date, source
    FROM macro
    WHERE indicator LIKE 'FX\\_%' ESCAPE '\\'
    ORDER BY indicator, reference_date DESC
""")


@router.get("", response_model=list[MacroOut])
async def list_macro(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(_LATEST_ALL_SQL)
    return [MacroOut.model_validate(dict(r)) for r in result.mappings().all()]


@router.get("/fx", response_model=list[MacroOut])
async def list_fx(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(_LATEST_FX_SQL)
    return [MacroOut.model_validate(dict(r)) for r in result.mappings().all()]

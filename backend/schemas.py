from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def _dec(v: Optional[Decimal]) -> Optional[str]:
    return str(v) if v is not None else None


class SecurityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    listing_date: Optional[date] = None
    status: Optional[str] = None
    description: Optional[str] = None


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    trade_time: datetime
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    last: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    close: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_pct: Optional[Decimal] = None
    volume: Optional[int] = None
    value: Optional[Decimal] = None
    bid_price: Optional[Decimal] = None
    bid_qty: Optional[int] = None
    ask_price: Optional[Decimal] = None
    ask_qty: Optional[int] = None

    @field_serializer("open", "high", "low", "last", "prev_close", "close",
                      "change", "change_pct", "value", "bid_price", "ask_price")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class OtcTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    bond_name: str
    trade_date: date
    price: Optional[Decimal] = None
    yield_: Optional[Decimal] = Field(None, alias="yield", serialization_alias="yield")
    volume: Optional[int] = None
    value: Optional[Decimal] = None
    market_type: Optional[str] = None
    currency: Optional[str] = None
    cbonds_id: Optional[int] = None

    @field_serializer("price", "value")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)

    @field_serializer("yield_")
    def serialize_yield(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class BondPriceHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    bond_name: str
    cbonds_id: Optional[int] = None
    trade_date: date
    price: Optional[Decimal] = None
    yield_: Optional[Decimal] = Field(None, alias="yield", serialization_alias="yield")
    currency: Optional[str] = None

    @field_serializer("price")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)

    @field_serializer("yield_")
    def serialize_yield(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class MacroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicator: str
    value: Optional[Decimal] = None
    reference_date: date
    source: Optional[str] = None

    @field_serializer("value")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class RegulatoryStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicator: str
    value: Optional[Decimal] = None
    unit: Optional[str] = None
    reference_year: int
    source: Optional[str] = None
    notes: Optional[str] = None

    @field_serializer("value")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class OtcBondRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bond_name: str
    board_category: Optional[str] = None
    sector: Optional[str] = None
    issue_date: Optional[date] = None
    currency: Optional[str] = None
    maturity_months: Optional[int] = None
    coupon_rate_raw: Optional[str] = None
    coupon_rate: Optional[Decimal] = None
    underwriter: Optional[str] = None
    status: Optional[str] = None
    scraped_date: date

    @field_serializer("coupon_rate")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return _dec(v)


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None

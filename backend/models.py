from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, Integer, Numeric, String, Text
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Security(Base):
    __tablename__ = "securities"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    isin: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    listing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(10), default="active")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    high: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    low: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    last: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    prev_close: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    bid_price: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    bid_qty: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ask_price: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    ask_qty: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    close: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    change: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)


class OtcTrade(Base):
    __tablename__ = "otc_trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bond_name: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    # 'yield' is a Python keyword — use yield_ as the attribute name
    yield_: Mapped[Optional[Decimal]] = mapped_column("yield", Numeric, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


class Macro(Base):
    __tablename__ = "macro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class RegulatoryStats(Base):
    __tablename__ = "regulatory_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

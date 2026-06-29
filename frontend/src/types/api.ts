// All NUMERIC DB columns arrive as string | null (Pydantic Decimal serializer).
// Integer columns (id, volume, bid_qty, ask_qty) arrive as number | null.

export interface Security {
  ticker: string;
  name: string | null;
  isin: string | null;
  sector: string | null;
  listing_date: string | null;
  status: string | null;
  description: string | null;
}

export interface Quote {
  id: number;
  ticker: string;
  trade_time: string;
  open: string | null;
  high: string | null;
  low: string | null;
  last: string | null;
  prev_close: string | null;
  close: string | null;
  change: string | null;
  change_pct: string | null;
  volume: number | null;
  value: string | null;
  bid_price: string | null;
  bid_qty: number | null;
  ask_price: string | null;
  ask_qty: number | null;
}

export interface OtcTrade {
  id: number;
  bond_name: string;
  trade_date: string;
  price: string | null;
  // 'yield' is a JS reserved word — access via bracket notation: trade["yield"]
  'yield': string | null;
  volume: number | null;
  value: string | null;
  market_type: string | null;
}

export interface OtcBondRegistry {
  id: number;
  bond_name: string;
  board_category: string | null;
  sector: string | null;
  issue_date: string | null;
  currency: string | null;
  maturity_months: number | null;
  coupon_rate_raw: string | null;
  coupon_rate: string | null;
  underwriter: string | null;
  status: string | null;
  scraped_date: string;
}

export interface MacroIndicator {
  id: number;
  indicator: string;
  value: string | null;
  reference_date: string;
  source: string | null;
}

export interface RegulatoryIndicator {
  id: number;
  indicator: string;
  value: string | null;
  unit: string | null;
  reference_year: number;
  source: string | null;
  notes: string | null;
}

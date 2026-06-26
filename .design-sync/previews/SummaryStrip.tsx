import { SummaryStrip } from 'frontend';

const QUOTES_MIXED = [
  { id: 1, ticker: 'APU', trade_time: '2026-06-25T09:00:00', last: '9200', change: '150', change_pct: '1.66', value: '250000000', open: '9050', high: '9250', low: '9000', prev_close: '9050', close: null, volume: 27174, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 2, ticker: 'MIK', trade_time: '2026-06-25T09:00:00', last: '3450', change: '-80', change_pct: '-2.27', value: '187000000', open: '3530', high: '3530', low: '3420', prev_close: '3530', close: null, volume: 54202, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 3, ticker: 'MBK', trade_time: '2026-06-25T09:00:00', last: '12400', change: '0', change_pct: '0.00', value: '99000000', open: '12400', high: '12500', low: '12300', prev_close: '12400', close: null, volume: 7983, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 4, ticker: 'MNDZ', trade_time: '2026-06-25T09:00:00', last: '1820', change: '40', change_pct: '2.25', value: '73000000', open: '1780', high: '1830', low: '1775', prev_close: '1780', close: null, volume: 40109, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 5, ticker: 'GOM', trade_time: '2026-06-25T09:00:00', last: '5100', change: '-120', change_pct: '-2.30', value: '61000000', open: '5220', high: '5220', low: '5090', prev_close: '5220', close: null, volume: 11961, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
];

const QUOTES_ALL_UP = QUOTES_MIXED.map((q) => ({ ...q, change: String(Math.abs(Number(q.change) || 50)), change_pct: '1.20' }));

export function MixedSession() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <SummaryStrip quotes={QUOTES_MIXED} />
    </div>
  );
}

export function BullishSession() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <SummaryStrip quotes={QUOTES_ALL_UP} />
    </div>
  );
}

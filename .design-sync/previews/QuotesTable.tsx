import { QuotesTable } from 'frontend';

const QUOTES = [
  { id: 1,  ticker: 'APU',   trade_time: '2026-06-25T09:00:00', last: '9200',  change: '150',  change_pct: '1.66',  value: '250200000', open: '9050',  high: '9250',  low: '9000',  prev_close: '9050',  close: null, volume: 27174, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 2,  ticker: 'MIK',   trade_time: '2026-06-25T09:00:00', last: '3450',  change: '-80',  change_pct: '-2.27', value: '187000000', open: '3530',  high: '3530',  low: '3420',  prev_close: '3530',  close: null, volume: 54202, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 3,  ticker: 'MBK',   trade_time: '2026-06-25T09:00:00', last: '12400', change: '0',    change_pct: '0.00',  value: '99300000',  open: '12400', high: '12500', low: '12300', prev_close: '12400', close: null, volume: 7983,  bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 4,  ticker: 'MNDZ',  trade_time: '2026-06-25T09:00:00', last: '1820',  change: '40',   change_pct: '2.25',  value: '73080000',  open: '1780',  high: '1830',  low: '1775',  prev_close: '1780',  close: null, volume: 40109, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 5,  ticker: 'GOM',   trade_time: '2026-06-25T09:00:00', last: '5100',  change: '-120', change_pct: '-2.30', value: '61200000',  open: '5220',  high: '5220',  low: '5090',  prev_close: '5220',  close: null, volume: 11961, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 6,  ticker: 'TDBM',  trade_time: '2026-06-25T09:00:00', last: '4200',  change: '60',   change_pct: '1.45',  value: '42000000',  open: '4140',  high: '4210',  low: '4130',  prev_close: '4140',  close: null, volume: 10000, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
  { id: 7,  ticker: 'BRT',   trade_time: '2026-06-25T09:00:00', last: '660',   change: '-15',  change_pct: '-2.22', value: '33000000',  open: '675',   high: '678',   low: '658',   prev_close: '675',   close: null, volume: 50000, bid_price: null, bid_qty: null, ask_price: null, ask_qty: null },
];

export function MarketQuotes() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <QuotesTable quotes={QUOTES} onSelectTicker={() => {}} />
    </div>
  );
}

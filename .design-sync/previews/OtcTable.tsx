import { OtcTable } from 'frontend';

const TRADES = [
  { id: 1, bond_name: 'GoM 2027 Bond', trade_date: '2026-06-25', price: '100.25', 'yield': '8.45', volume: 500000, value: '501250000', market_type: 'OTC' },
  { id: 2, bond_name: 'BOM Discount Bond 2028', trade_date: '2026-06-25', price: '98.50', 'yield': '9.12', volume: 300000, value: '295500000', market_type: 'OTC' },
  { id: 3, bond_name: 'MCS Housing Bond 2026', trade_date: '2026-06-24', price: '101.10', 'yield': '7.80', volume: 200000, value: '202200000', market_type: 'OTC' },
  { id: 4, bond_name: 'Ulaanbaatar City Bond 2029', trade_date: '2026-06-24', price: '99.75', 'yield': '9.55', volume: 150000, value: '149625000', market_type: 'OTC' },
];

const EMPTY: typeof TRADES = [];

export function BondTrades() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <OtcTable trades={TRADES} />
    </div>
  );
}

export function Empty() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <OtcTable trades={EMPTY} />
    </div>
  );
}

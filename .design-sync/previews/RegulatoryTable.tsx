import { RegulatoryTable } from 'frontend';

const STATS = [
  { id: 1, indicator: 'policy_rate',           value: '12.00', unit: 'percent', reference_year: 2026, source: 'BOM',  notes: null },
  { id: 2, indicator: 'broker_count',           value: '18',    unit: 'count',   reference_year: 2025, source: 'FRC',  notes: null },
  { id: 3, indicator: 'market_cap_mnt',         value: '4870000000000', unit: 'MNT', reference_year: 2025, source: 'MASD', notes: null },
  { id: 4, indicator: 'listed_companies_count', value: '255',   unit: 'count',   reference_year: 2025, source: 'MSE',  notes: null },
];

export function FrcStats() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <RegulatoryTable stats={STATS} />
    </div>
  );
}

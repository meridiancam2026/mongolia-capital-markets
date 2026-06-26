import { MarketStatsCards } from 'frontend';

const INDICATORS = [
  { id: 1, indicator: 'MASD_SECONDARY_MARKET_MNT', value: '47850000000', reference_date: '2026-05-31', source: 'MASD' },
  { id: 2, indicator: 'MASD_PRIMARY_MARKET_MNT',   value: '12340000000', reference_date: '2026-05-31', source: 'MASD' },
  { id: 3, indicator: 'MASD_OTC_BOND_BALANCE_MNT', value: '380000000000', reference_date: '2026-05-31', source: 'MASD' },
];

export function MasdTotals() {
  return (
    <div style={{ padding: '24px', background: '#f9fafb' }}>
      <MarketStatsCards indicators={INDICATORS} />
    </div>
  );
}

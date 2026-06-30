import { useState } from 'react';
import { OtcTable } from '../components/otc/OtcTable';
import { BondHistoryChart } from '../components/otc/BondHistoryChart';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';
import type { OtcTrade } from '../types/api';

const S = {
  faint: '#8a977c',
} as const;

function SectionHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: S.faint, letterSpacing: '0.1em' }}>
        {title}
      </div>
      <div style={{ fontSize: 9, color: S.faint, marginTop: 2, letterSpacing: '0.04em' }}>
        {sub}
      </div>
    </div>
  );
}

export function EurobondsView() {
  const prices = useOtc('eurobond');
  const [selectedBond, setSelectedBond] = useState<string | null>(null);

  function handleRowClick(trade: OtcTrade) {
    setSelectedBond((prev) => (prev === trade.bond_name ? null : trade.bond_name));
  }

  return (
    <div>
      <SectionHeader
        title="MONGOLIAN EUROBONDS · INDICATIVE PRICES"
        sub="USD / JPY / foreign-currency bonds · Click a row to view 90-day price & yield history · Source: Cbonds"
      />
      {prices.error && <ErrorBanner message={prices.error} />}
      {prices.loading ? (
        <Spinner />
      ) : (
        <OtcTable
          trades={prices.data}
          onRowClick={handleRowClick}
          selectedBondName={selectedBond}
        />
      )}
      {selectedBond && (
        <div style={{ marginTop: 12 }}>
          <BondHistoryChart
            bondName={selectedBond}
            onClose={() => setSelectedBond(null)}
          />
        </div>
      )}
    </div>
  );
}

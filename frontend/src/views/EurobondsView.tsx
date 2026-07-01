import { useState, useCallback } from 'react';
import { OtcTable } from '../components/otc/OtcTable';
import { BondHistoryChart } from '../components/otc/BondHistoryChart';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';
import { apiPost, apiFetch, pollUntilChanged } from '../api/client';
import type { OtcTrade } from '../types/api';

const S = {
  faint:   '#8a977c',
  border:  '#d3dcc6',
  surface: '#f4f7f1',
  muted:   '#5d6a52',
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
  const [refreshing, setRefreshing] = useState(false);

  function handleRowClick(trade: OtcTrade) {
    setSelectedBond((prev) => (prev === trade.bond_name ? null : trade.bond_name));
  }

  const refresh = useCallback(async () => {
    setRefreshing(true);
    const snapshot = prices.data[0]?.price ?? prices.data[0]?.['yield'] ?? null;
    try {
      await apiPost('/api/admin/trigger/ingest_cbonds');
    } catch { /* non-fatal */ }
    const fresh = await pollUntilChanged(
      () => apiFetch<OtcTrade[]>('/api/otc?segment=eurobond'),
      (rows) => (rows[0]?.price ?? rows[0]?.['yield'] ?? null) !== snapshot,
    );
    if (fresh) {
      prices.refetch();
    }
    setRefreshing(false);
  }, [prices]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <SectionHeader
          title="MONGOLIAN EUROBONDS · INDICATIVE PRICES"
          sub="USD / JPY / foreign-currency bonds · Click a row to view 90-day price & yield history · Source: Cbonds"
        />
        <button
          onClick={refresh}
          disabled={refreshing}
          title="Trigger Cbonds ingest and refresh bond prices"
          style={{
            fontSize: 9,
            letterSpacing: '0.08em',
            fontFamily: "'IBM Plex Mono', monospace",
            fontWeight: 600,
            color: refreshing ? S.faint : S.muted,
            background: S.surface,
            border: `1px solid ${S.border}`,
            padding: '3px 10px',
            cursor: refreshing ? 'not-allowed' : 'pointer',
            opacity: refreshing ? 0.6 : 1,
            flexShrink: 0,
          }}
        >
          {refreshing ? 'REFRESHING…' : '↺ REFRESH'}
        </button>
      </div>
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

import { useState, useCallback } from 'react';
import type { OtcTrade } from '../types/api';
import { OtcTable } from '../components/otc/OtcTable';
import { OtcRegistryTable } from '../components/otc/OtcRegistryTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';
import { useOtcRegistry } from '../hooks/useOtcRegistry';
import { apiPost, apiFetch, pollUntilChanged } from '../api/client';

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

export function LocalBondsView() {
  const prices = useOtc('local');
  const registry = useOtcRegistry();
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    const snapshot = prices.data[0]?.price ?? prices.data[0]?.['yield'] ?? null;
    try {
      await apiPost('/api/admin/trigger/ingest_cbonds');
    } catch { /* non-fatal */ }
    const fresh = await pollUntilChanged(
      () => apiFetch<OtcTrade[]>('/api/otc?segment=local'),
      (rows) => (rows[0]?.price ?? rows[0]?.['yield'] ?? null) !== snapshot,
    );
    if (fresh) {
      prices.refetch();
    }
    setRefreshing(false);
  }, [prices]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      <div>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <SectionHeader
            title="LOCAL BOND MARKET · INDICATIVE PRICES"
            sub="MNT-denominated bonds · Indicative prices &amp; yields · Source: Cbonds"
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
        {prices.loading ? <Spinner /> : <OtcTable trades={prices.data} />}
      </div>

      <div style={{ borderTop: `1px solid ${S.border}` }} />

      <div>
        <SectionHeader
          title="M-OTC BOND REGISTRY"
          sub="All registered bonds with coupon rates and maturities · Source: masd.mn/otc/board"
        />
        {registry.error && <ErrorBanner message={registry.error} />}
        {registry.loading ? <Spinner /> : <OtcRegistryTable bonds={registry.data} />}
      </div>

    </div>
  );
}

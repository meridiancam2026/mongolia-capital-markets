import { OtcTable } from '../components/otc/OtcTable';
import { OtcRegistryTable } from '../components/otc/OtcRegistryTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';
import { useOtcRegistry } from '../hooks/useOtcRegistry';

const S = {
  faint:  '#8a977c',
  border: '#d3dcc6',
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      <div>
        <SectionHeader
          title="LOCAL BOND MARKET · INDICATIVE PRICES"
          sub="MNT-denominated bonds · Indicative prices &amp; yields · Source: Cbonds"
        />
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

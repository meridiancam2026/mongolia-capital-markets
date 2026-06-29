import { OtcTable } from '../components/otc/OtcTable';
import { OtcRegistryTable } from '../components/otc/OtcRegistryTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';
import { useOtcRegistry } from '../hooks/useOtcRegistry';

const S = {
  faint:  '#8a977c',
  muted:  '#5d6a52',
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

export function OtcView() {
  const leaderboard = useOtc();
  const registry = useOtcRegistry();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* Top-5 most active bonds (today's leaderboard) */}
      <div>
        <SectionHeader
          title="OTC BOND MARKET · TODAY'S MOST ACTIVE"
          sub="Top bonds by aggregate trade value · MASD M-OTC"
        />
        {leaderboard.error && <ErrorBanner message={leaderboard.error} />}
        {leaderboard.loading ? <Spinner /> : <OtcTable trades={leaderboard.data} />}
      </div>

      {/* Divider */}
      <div style={{ borderTop: `1px solid ${S.border}` }} />

      {/* Full bond registry */}
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

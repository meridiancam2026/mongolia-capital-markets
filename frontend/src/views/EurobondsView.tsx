import { OtcTable } from '../components/otc/OtcTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';

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

  return (
    <div>
      <SectionHeader
        title="MONGOLIAN EUROBONDS · INDICATIVE PRICES"
        sub="USD / JPY / foreign-currency bonds issued by Mongolian entities · Source: Cbonds"
      />
      {prices.error && <ErrorBanner message={prices.error} />}
      {prices.loading ? <Spinner /> : <OtcTable trades={prices.data} />}
    </div>
  );
}

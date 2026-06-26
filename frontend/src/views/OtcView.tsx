import { OtcTable } from '../components/otc/OtcTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useOtc } from '../hooks/useOtc';

export function OtcView() {
  const { data, loading, error } = useOtc();

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: '#8a977c', letterSpacing: '0.1em' }}>
          OTC BOND MARKET
        </div>
        <div style={{ fontSize: 9, color: '#8a977c', marginTop: 2, letterSpacing: '0.04em' }}>
          Over-the-counter bond trades · MASD M-OTC
        </div>
      </div>
      {error && <ErrorBanner message={error} />}
      {loading ? <Spinner /> : <OtcTable trades={data} />}
    </div>
  );
}

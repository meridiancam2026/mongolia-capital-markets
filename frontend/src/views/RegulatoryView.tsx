import { RegulatoryTable } from '../components/regulatory/RegulatoryTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useRegulatory } from '../hooks/useRegulatory';

export function RegulatoryView() {
  const { data, loading, error } = useRegulatory();

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: '#8a977c', letterSpacing: '0.1em' }}>
          REGULATORY &amp; STRUCTURAL INDICATORS
        </div>
        <div style={{ fontSize: 9, color: '#8a977c', marginTop: 2, letterSpacing: '0.04em' }}>
          Annual statistics · FRC / MASD / BOM
        </div>
      </div>
      {error && <ErrorBanner message={error} />}
      {loading ? <Spinner /> : <RegulatoryTable stats={data} />}
    </div>
  );
}

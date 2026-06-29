import { FxCard } from '../components/macro/FxCard';
import { MarketStatsCards } from '../components/macro/MarketStatsCards';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useFx } from '../hooks/useFx';
import { useMacro } from '../hooks/useMacro';

const S = {
  faint:   '#8a977c',
  border:  '#d3dcc6',
  surface: '#f4f7f1',
  muted:   '#5d6a52',
} as const;

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ fontSize: 9, fontWeight: 600, color: S.faint, letterSpacing: '0.1em', marginBottom: 12 }}>
      {children}
    </div>
  );
}

export function MacroView() {
  const { data: fxRates, loading: fxLoading, error: fxError } = useFx();
  const { data: allMacro, loading: macroLoading, error: macroError } = useMacro();

  const loading = fxLoading || macroLoading;
  const error = fxError || macroError;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: S.faint, letterSpacing: '0.1em' }}>MACRO</div>
        <div style={{ fontSize: 9, color: S.faint, marginTop: 2, letterSpacing: '0.04em' }}>
          FX rates &amp; market totals · BOM / MASD
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <Spinner />
      ) : (
        <>
          <section style={{ marginBottom: 28 }}>
            <SectionLabel>FX RATES VS MNT — BANK OF MONGOLIA REFERENCE</SectionLabel>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(168px, 1fr))',
              gap: 8,
            }}>
              {fxRates.map((r) => (
                <FxCard key={r.indicator} indicator={r} />
              ))}
            </div>
          </section>

          <div style={{ borderTop: `1px solid ${S.border}`, margin: '0 0 24px' }} />

          <section>
            <SectionLabel>MACRO INDICATORS — MARKET TOTALS · INFLATION · FX RESERVES</SectionLabel>
            <MarketStatsCards indicators={allMacro} />
          </section>
        </>
      )}
    </div>
  );
}

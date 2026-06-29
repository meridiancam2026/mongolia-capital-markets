import { useState } from 'react';
import { SummaryStrip } from '../components/market/SummaryStrip';
import { QuotesTable } from '../components/market/QuotesTable';
import { PriceHistoryChart } from '../components/market/PriceHistoryChart';
import { Modal } from '../components/ui/Modal';
import { Spinner } from '../components/ui/Spinner';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useQuotes } from '../hooks/useQuotes';
import { useSecurities } from '../hooks/useSecurities';

export function MarketView() {
  const { data, loading, error, lastUpdated } = useQuotes();
  const securities = useSecurities();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  return (
    <div>
      {/* Section header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: '#8a977c', letterSpacing: '0.1em' }}>
            MSE EQUITIES
          </div>
          <div style={{ fontSize: 9, color: '#8a977c', marginTop: 2, letterSpacing: '0.04em' }}>
            Mongolian Stock Exchange · click a row for price history
          </div>
        </div>
        {lastUpdated && (
          <span style={{
            fontSize: 9, color: '#8a977c', letterSpacing: '0.05em',
            border: '1px solid #d3dcc6', padding: '3px 8px',
            background: '#f4f7f1',
          }}>
            {lastUpdated.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} · 60s
          </span>
        )}
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <Spinner />
      ) : (
        <>
          <SummaryStrip quotes={data} />
          <QuotesTable quotes={data} securities={securities} onSelectTicker={setSelectedTicker} />
        </>
      )}

      {selectedTicker && (
        <Modal
          title={(() => {
            const sec = securities.get(selectedTicker);
            return sec?.name ? `${selectedTicker} · ${sec.name} — Price History` : `${selectedTicker} — Price History`;
          })()}
          onClose={() => setSelectedTicker(null)}
        >
          <PriceHistoryChart ticker={selectedTicker} />
        </Modal>
      )}
    </div>
  );
}

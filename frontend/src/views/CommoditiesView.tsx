import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { CommodityCard } from '../components/macro/CommodityCard';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { Spinner } from '../components/ui/Spinner';
import { useCommodities } from '../hooks/useCommodities';
import { useCommodityHistory } from '../hooks/useCommodityHistory';
import type { MacroIndicator } from '../types/api';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
);

// Display order for the three commodity panels
const COMMODITY_ORDER = [
  'COMMODITY_COPPER_USD_MT',
  'COMMODITY_GOLD_USD_OZ',
  'COMMODITY_COAL_PROXY_HKD',
] as const;

const S = {
  faint:   '#8a977c',
  border:  '#d3dcc6',
  surface: '#f4f7f1',
  muted:   '#5d6a52',
  text:    '#1f2a18',
} as const;

// Chart options shared across all commodity panels
const CHART_OPTIONS = {
  responsive: true,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: '#1f2a18',
      titleColor: '#8a977c',
      bodyColor: '#e6ede1',
      padding: 10,
      cornerRadius: 0,
      borderColor: '#d3dcc6',
      borderWidth: 1,
      titleFont: { family: "'IBM Plex Mono', monospace", size: 10 },
      bodyFont: { family: "'IBM Plex Mono', monospace", size: 11 },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#8a977c', font: { family: "'IBM Plex Mono', monospace", size: 9 } },
      border: { color: '#d3dcc6' },
    },
    y: {
      grid: { color: '#e2e8da' },
      ticks: { color: '#8a977c', font: { family: "'IBM Plex Mono', monospace", size: 9 } },
      border: { color: '#d3dcc6' },
    },
  },
};

function formatMonthLabel(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

interface PanelProps {
  indicatorCode: string;
  latest: MacroIndicator | undefined;
}

function CommodityPanel({ indicatorCode, latest }: PanelProps) {
  const { data: history, loading: histLoading } = useCommodityHistory(indicatorCode);

  // Month-over-month % change from last two history entries
  const changePct = history.length >= 2
    ? (() => {
        const prev = parseFloat(history[history.length - 2].value ?? '0');
        const curr = parseFloat(history[history.length - 1].value ?? '0');
        return prev > 0 ? ((curr - prev) / prev) * 100 : null;
      })()
    : null;

  const lineColor = changePct == null || changePct >= 0 ? '#2f8f4e' : '#c4453b';
  const fillColor = changePct == null || changePct >= 0
    ? 'rgba(47,143,78,0.08)'
    : 'rgba(196,69,59,0.06)';

  const chartData = {
    labels: history.map((h) => formatMonthLabel(h.reference_date)),
    datasets: [{
      label: indicatorCode,
      data: history.map((h) => h.value != null ? parseFloat(h.value) : null),
      spanGaps: false,
      fill: true,
      tension: 0.3,
      borderColor: lineColor,
      backgroundColor: fillColor,
      borderWidth: 1.5,
      pointRadius: 2,
      pointHoverRadius: 4,
      pointHoverBackgroundColor: lineColor,
    }],
  };

  return (
    <div style={{
      display: 'flex',
      gap: 16,
      marginBottom: 20,
      padding: '16px',
      background: S.surface,
      border: `1px solid ${S.border}`,
    }}>
      {/* Left: summary card */}
      {latest ? (
        <CommodityCard indicator={latest} changePct={changePct} />
      ) : (
        <div style={{ minWidth: 180, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: 10, color: S.faint, letterSpacing: '0.06em' }}>NO DATA</span>
        </div>
      )}

      {/* Right: trend chart */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {histLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
            <span style={{ fontSize: 9, color: S.faint, letterSpacing: '0.08em' }}>LOADING HISTORY…</span>
          </div>
        ) : history.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
            <span style={{ fontSize: 9, color: S.faint, letterSpacing: '0.08em' }}>NO HISTORY AVAILABLE</span>
          </div>
        ) : (
          <Line data={chartData} options={CHART_OPTIONS} />
        )}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ fontSize: 9, fontWeight: 600, color: S.faint, letterSpacing: '0.1em', marginBottom: 12 }}>
      {children}
    </div>
  );
}

export function CommoditiesView() {
  const { data: latest, loading, error } = useCommodities();

  const latestByCode = Object.fromEntries(latest.map((d) => [d.indicator, d]));

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: S.faint, letterSpacing: '0.1em' }}>COMMODITIES</div>
        <div style={{ fontSize: 9, color: S.faint, marginTop: 2, letterSpacing: '0.04em' }}>
          Spot prices &amp; market proxies · monthly · Yahoo Finance
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <Spinner />
      ) : (
        <>
          <section>
            <SectionLabel>MONGOLIAN EXPORT COMMODITIES — SPOT PRICES &amp; PROXIES</SectionLabel>
            {COMMODITY_ORDER.map((code) => (
              <CommodityPanel
                key={code}
                indicatorCode={code}
                latest={latestByCode[code]}
              />
            ))}
          </section>

          <div style={{
            marginTop: 16,
            padding: '10px 12px',
            background: S.surface,
            border: `1px solid ${S.border}`,
            fontSize: 9,
            color: S.faint,
            letterSpacing: '0.04em',
          }}>
            SOURCE: Yahoo Finance · Copper: COMEX HG=F ($/MT) · Gold: COMEX GC=F ($/troy oz) ·
            Coal proxy: Yankuang Energy 1171.HK (HKD/share) — tracks China coal demand · Updated monthly
          </div>
        </>
      )}
    </div>
  );
}

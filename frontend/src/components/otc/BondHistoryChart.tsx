import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useBondHistory } from '../../hooks/useBondHistory';
import { Spinner } from '../ui/Spinner';
import { ErrorBanner } from '../ui/ErrorBanner';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const S = {
  text:   '#1f2a18',
  muted:  '#5d6a52',
  faint:  '#8a977c',
  border: '#d3dcc6',
  surface:'#f4f7f1',
  green:  '#2f8f4e',
  teal:   '#2a7f8a',
} as const;

interface Props {
  bondName: string;
  onClose: () => void;
}

export function BondHistoryChart({ bondName, onClose }: Props) {
  const { data, loading, error } = useBondHistory(bondName);

  const labels = data.map((d) => d.trade_date);
  const prices = data.map((d) => (d.price != null ? parseFloat(d.price) : null));
  const yields = data.map((d) => (d['yield'] != null ? parseFloat(d['yield']) : null));

  const hasPrice = prices.some((v) => v != null);
  const hasYield = yields.some((v) => v != null);

  const datasets = [
    ...(hasPrice ? [{
      label: 'Price',
      data: prices,
      borderColor: S.green,
      backgroundColor: S.green + '22',
      tension: 0.3,
      pointRadius: 2,
      yAxisID: 'yPrice',
    }] : []),
    ...(hasYield ? [{
      label: 'Yield (%)',
      data: yields,
      borderColor: S.teal,
      backgroundColor: S.teal + '22',
      tension: 0.3,
      pointRadius: 2,
      yAxisID: 'yYield',
    }] : []),
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        labels: {
          color: S.muted,
          font: { family: "'IBM Plex Mono', monospace", size: 10 },
        },
      },
      tooltip: {
        backgroundColor: S.surface,
        titleColor: S.text,
        bodyColor: S.muted,
        borderColor: S.border,
        borderWidth: 1,
        titleFont: { family: "'IBM Plex Mono', monospace", size: 10 },
        bodyFont: { family: "'IBM Plex Mono', monospace", size: 10 },
      },
    },
    scales: {
      x: {
        ticks: {
          color: S.faint,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
          maxTicksLimit: 10,
        },
        grid: { color: S.border },
      },
      yPrice: {
        type: 'linear' as const,
        display: hasPrice,
        position: 'left' as const,
        ticks: {
          color: S.green,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
        },
        grid: { color: S.border },
      },
      yYield: {
        type: 'linear' as const,
        display: hasYield,
        position: 'right' as const,
        ticks: {
          color: S.teal,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
        },
        grid: { drawOnChartArea: false },
      },
    },
  };

  return (
    <div style={{
      background: S.surface,
      border: `1px solid ${S.border}`,
      borderRadius: 4,
      padding: '14px 16px',
      marginTop: 4,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: S.muted, letterSpacing: '0.08em' }}>
            90-DAY PRICE &amp; YIELD HISTORY
          </div>
          <div style={{ fontSize: 9, color: S.faint, marginTop: 2 }}>{bondName}</div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: S.faint, fontSize: 14, padding: '2px 6px',
            fontFamily: 'inherit',
          }}
        >
          ✕
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spinner /></div>}
      {!loading && !error && data.length === 0 && (
        <div style={{ fontSize: 10, color: S.faint, textAlign: 'center', padding: '30px 0' }}>
          No history data available yet — run ingest to populate.
        </div>
      )}
      {!loading && data.length > 0 && (
        <div style={{ height: 220 }}>
          <Line data={{ labels, datasets }} options={options} />
        </div>
      )}
    </div>
  );
}

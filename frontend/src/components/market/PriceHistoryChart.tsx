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
import { useTickerHistory } from '../../hooks/useTickerHistory';
import { formatChange, formatPct } from '../../utils/format';
import { Spinner } from '../ui/Spinner';
import { ErrorBanner } from '../ui/ErrorBanner';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
);

interface Props {
  ticker: string;
}

export function PriceHistoryChart({ ticker }: Props) {
  const { data, loading, error } = useTickerHistory(ticker);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (data.length === 0) return (
    <div style={{ fontSize: 11, color: '#8a977c', padding: '20px 0', letterSpacing: '0.06em' }}>
      NO PRICE HISTORY AVAILABLE
    </div>
  );

  const chronological = data.slice().reverse();
  const latest = data[0];

  const change = latest.change != null ? parseFloat(latest.change) : 0;
  const lineColor  = change >= 0 ? '#2f8f4e' : '#c4453b';
  const fillColor  = change >= 0 ? 'rgba(47,143,78,0.08)' : 'rgba(196,69,59,0.06)';
  const chgColor   = change > 0 ? '#2f8f4e' : change < 0 ? '#c4453b' : '#8a977c';

  const chartData = {
    labels: chronological.map((q) =>
      new Date(q.trade_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ),
    datasets: [
      {
        label: `${ticker} Last`,
        data: chronological.map((q) => (q.last != null ? parseFloat(q.last) : null)),
        spanGaps: false,
        fill: true,
        tension: 0.25,
        borderColor: lineColor,
        backgroundColor: fillColor,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 3,
        pointHoverBackgroundColor: lineColor,
      },
    ],
  };

  const options = {
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

  return (
    <div style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
      {/* Stats row */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
        <span style={{ fontSize: 26, fontWeight: 600, color: '#1f2a18', letterSpacing: '-0.02em' }}>
          {latest.last ?? '—'}
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: chgColor }}>
          {formatChange(latest.change)} ({formatPct(latest.change_pct)})
        </span>
        <span style={{ fontSize: 9, color: '#8a977c', marginLeft: 'auto', letterSpacing: '0.04em' }}>
          {new Date(latest.trade_time).toLocaleString('en-GB')}
        </span>
      </div>
      <Line data={chartData} options={options} />
    </div>
  );
}

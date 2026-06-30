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
import { useEquityHistory } from '../../hooks/useEquityHistory';
import { Spinner } from '../ui/Spinner';
import { ErrorBanner } from '../ui/ErrorBanner';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
);

const S = {
  text:   '#1f2a18',
  muted:  '#5d6a52',
  faint:  '#8a977c',
  border: '#d3dcc6',
  green:  '#2f8f4e',
  red:    '#c4453b',
} as const;

interface Props {
  ticker: string;
}

export function PriceHistoryChart({ ticker }: Props) {
  const { data, loading, error } = useEquityHistory(ticker);

  if (loading) return <Spinner />;
  if (error)   return <ErrorBanner message={error} />;

  if (data.length === 0) return (
    <div style={{ fontSize: 11, color: S.faint, padding: '20px 0', letterSpacing: '0.06em' }}>
      NO PRICE HISTORY YET — data accumulates daily after each MSE scrape.
    </div>
  );

  const latest = data[data.length - 1];
  const change = latest.change != null ? parseFloat(latest.change) : 0;
  const lineColor = change >= 0 ? S.green : S.red;
  const fillColor = change >= 0 ? 'rgba(47,143,78,0.08)' : 'rgba(196,69,59,0.06)';
  const chgColor  = change > 0 ? S.green : change < 0 ? S.red : S.faint;

  const chartData = {
    labels: data.map((d) =>
      new Date(d.trade_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ),
    datasets: [
      {
        label: `${ticker} Close`,
        data: data.map((d) => (d.close != null ? parseFloat(d.close) : null)),
        spanGaps: false,
        fill: true,
        tension: 0.25,
        borderColor: lineColor,
        backgroundColor: fillColor,
        borderWidth: 1.5,
        pointRadius: data.length > 60 ? 0 : 2,
        pointHoverRadius: 4,
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
        backgroundColor: S.text,
        titleColor: S.faint,
        bodyColor: '#e6ede1',
        padding: 10,
        cornerRadius: 0,
        borderColor: S.border,
        borderWidth: 1,
        titleFont: { family: "'IBM Plex Mono', monospace", size: 10 },
        bodyFont:  { family: "'IBM Plex Mono', monospace", size: 11 },
        callbacks: {
          label: (ctx: { parsed: { y: number | null } }) =>
            ctx.parsed.y != null ? `Close: ${ctx.parsed.y.toLocaleString()}` : '',
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: S.faint,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
          maxTicksLimit: 12,
          maxRotation: 0,
        },
        border: { color: S.border },
      },
      y: {
        grid: { color: '#e2e8da' },
        ticks: { color: S.faint, font: { family: "'IBM Plex Mono', monospace", size: 9 } },
        border: { color: S.border },
      },
    },
  };

  const fmtChange = (v: string | null) => {
    if (v == null) return '—';
    const n = parseFloat(v);
    return (n >= 0 ? '+' : '') + n.toLocaleString();
  };
  const fmtPct = (v: string | null) => {
    if (v == null) return '';
    return `(${parseFloat(v).toFixed(2)}%)`;
  };

  return (
    <div style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
        <span style={{ fontSize: 26, fontWeight: 600, color: S.text, letterSpacing: '-0.02em' }}>
          {latest.close ?? '—'}
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: chgColor }}>
          {fmtChange(latest.change)} {fmtPct(latest.change_pct)}
        </span>
        <span style={{ fontSize: 9, color: S.faint, marginLeft: 'auto', letterSpacing: '0.04em' }}>
          {data.length} days · {latest.trade_date}
        </span>
      </div>
      <Line data={chartData} options={options} />
    </div>
  );
}

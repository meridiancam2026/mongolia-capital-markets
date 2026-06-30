import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useBondHistory } from '../../hooks/useBondHistory';
import { Spinner } from '../ui/Spinner';
import { ErrorBanner } from '../ui/ErrorBanner';
import type { BondPriceHistory } from '../../types/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

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

// ── Interpolation helpers ──────────────────────────────────────────────────

function dateRange(from: string, to: string): string[] {
  const dates: string[] = [];
  const cur = new Date(from);
  const end = new Date(to);
  while (cur <= end) {
    dates.push(cur.toISOString().slice(0, 10));
    cur.setDate(cur.getDate() + 1);
  }
  return dates;
}

function interpolate(
  allDates: string[],
  known: Map<string, number>,
): (number | null)[] {
  const result: (number | null)[] = allDates.map((d) => known.get(d) ?? null);

  // Linear interpolation across interior gaps
  let i = 0;
  while (i < result.length) {
    if (result[i] === null) {
      // find previous known index
      let prev = i - 1;
      while (prev >= 0 && result[prev] === null) prev--;
      // find next known index
      let next = i + 1;
      while (next < result.length && result[next] === null) next++;

      if (prev >= 0 && next < result.length) {
        // interpolate between prev and next
        const v0 = result[prev] as number;
        const v1 = result[next] as number;
        const span = next - prev;
        for (let k = prev + 1; k < next; k++) {
          result[k] = v0 + (v1 - v0) * ((k - prev) / span);
        }
        i = next;
      } else {
        i++;
      }
    } else {
      i++;
    }
  }
  return result;
}

function buildSeries(data: BondPriceHistory[]) {
  if (data.length === 0) return { labels: [], yields: [], prices: [] };

  const sorted = [...data].sort((a, b) => a.trade_date.localeCompare(b.trade_date));
  const allDates = dateRange(sorted[0].trade_date, sorted[sorted.length - 1].trade_date);

  const yieldMap = new Map<string, number>();
  const priceMap = new Map<string, number>();
  for (const row of sorted) {
    if (row['yield'] != null) yieldMap.set(row.trade_date, parseFloat(row['yield']));
    if (row.price  != null) priceMap.set(row.trade_date, parseFloat(row.price));
  }

  return {
    labels: allDates,
    yields: interpolate(allDates, yieldMap),
    prices: interpolate(allDates, priceMap),
  };
}

// ── Component ─────────────────────────────────────────────────────────────

export function BondHistoryChart({ bondName, onClose }: Props) {
  const { data, loading, error } = useBondHistory(bondName);

  const { labels, yields, prices } = buildSeries(data);

  const hasPrice = prices.some((v) => v != null);
  const hasYield = yields.some((v) => v != null);

  const datasets = [
    ...(hasYield ? [{
      label: 'Yield (%)',
      data: yields,
      borderColor: S.teal,
      backgroundColor: S.teal + '18',
      fill: true,
      tension: 0.35,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 1.5,
      yAxisID: 'yYield',
    }] : []),
    ...(hasPrice ? [{
      label: 'Price',
      data: prices,
      borderColor: S.green,
      backgroundColor: S.green + '18',
      fill: true,
      tension: 0.35,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 1.5,
      yAxisID: 'yPrice',
    }] : []),
  ];

  const dataCount = data.length;
  const interpCount = labels.length - dataCount;

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        labels: {
          color: S.muted,
          font: { family: "'IBM Plex Mono', monospace", size: 10 },
          boxWidth: 10,
        },
      },
      tooltip: {
        backgroundColor: '#ffffff',
        titleColor: S.text,
        bodyColor: S.muted,
        borderColor: S.border,
        borderWidth: 1,
        titleFont: { family: "'IBM Plex Mono', monospace", size: 10 },
        bodyFont: { family: "'IBM Plex Mono', monospace", size: 10 },
        callbacks: {
          label: (ctx: { dataset: { label?: string }; parsed: { y: number | null } }) => {
            if (ctx.parsed.y == null) return '';
            const lbl = ctx.dataset.label ?? '';
            return lbl.includes('Yield')
              ? `${lbl}: ${ctx.parsed.y.toFixed(2)}%`
              : `${lbl}: ${ctx.parsed.y.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: S.faint,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
          maxTicksLimit: 12,
          maxRotation: 0,
        },
        grid: { color: S.border + '80' },
      },
      yYield: {
        type: 'linear' as const,
        display: hasYield,
        position: 'left' as const,
        ticks: {
          color: S.teal,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
          callback: (v: number | string) => `${Number(v).toFixed(1)}%`,
        },
        grid: { color: S.border + '80' },
      },
      yPrice: {
        type: 'linear' as const,
        display: hasPrice,
        position: hasYield ? 'right' as const : 'left' as const,
        ticks: {
          color: S.green,
          font: { family: "'IBM Plex Mono', monospace", size: 9 },
        },
        grid: { drawOnChartArea: !hasYield },
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
            YIELD HISTORY
          </div>
          <div style={{ fontSize: 9, color: S.faint, marginTop: 2 }}>
            {bondName}
            {interpCount > 0 && (
              <span style={{ marginLeft: 8, color: S.faint }}>
                · {dataCount} obs · {interpCount} interpolated
              </span>
            )}
          </div>
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
      {loading && (
        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spinner />
        </div>
      )}
      {!loading && !error && data.length === 0 && (
        <div style={{ fontSize: 10, color: S.faint, textAlign: 'center', padding: '30px 0' }}>
          No history data yet — import CSV or wait for next daily ingest.
        </div>
      )}
      {!loading && data.length > 0 && (
        <div style={{ height: 240 }}>
          <Line data={{ labels, datasets }} options={options} />
        </div>
      )}
    </div>
  );
}

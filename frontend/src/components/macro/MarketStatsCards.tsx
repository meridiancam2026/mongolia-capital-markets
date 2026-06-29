import type { MacroIndicator } from '../../types/api';
import { formatMNT } from '../../utils/format';

interface Props {
  indicators: MacroIndicator[];
}

interface StatConfig {
  label: string;
  color: string;
  tag: string;
  format?: (v: string | null) => string;
}

const STAT_CONFIG: Record<string, StatConfig> = {
  MASD_SECONDARY_MARKET_MNT: { label: 'Secondary Market',    color: '#2b6cb0', tag: 'SEC' },
  MASD_PRIMARY_MARKET_MNT:   { label: 'Primary Market',      color: '#2f8f4e', tag: 'PRI' },
  MASD_OTC_BOND_BALANCE_MNT: { label: 'OTC Bond Balance',    color: '#b07d18', tag: 'OTC' },
  INFLATION_CPI_YOY: {
    label: 'Inflation (CPI YoY)',
    color: '#c4453b',
    tag: 'CPI',
    format: (v) => v != null ? `${parseFloat(v).toFixed(1)}%` : '—',
  },
  FOREIGN_RESERVES_USD_MN: {
    label: 'FX Reserves',
    color: '#2b6cb0',
    tag: 'RES',
    format: (v) => v != null
      ? `$${parseFloat(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}mn`
      : '—',
  },
};

const S = {
  border:  '#cbd6bb',
  row:     '#e2e8da',
  text:    '#1f2a18',
  faint:   '#8a977c',
  muted:   '#5d6a52',
} as const;

export function MarketStatsCards({ indicators }: Props) {
  const stats = indicators.filter((i) => i.indicator in STAT_CONFIG);
  if (stats.length === 0) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
      {stats.map((s) => {
        const cfg = STAT_CONFIG[s.indicator];
        return (
          <div key={s.indicator} style={{
            background: '#ffffff',
            border: `1px solid ${S.border}`,
            padding: '16px 18px',
            fontFamily: "'IBM Plex Mono', monospace",
          }}>
            {/* Tag + label */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <span style={{
                fontSize: 8, fontWeight: 700, letterSpacing: '0.1em',
                color: cfg.color,
                border: `1px solid ${cfg.color}`,
                padding: '2px 5px',
                opacity: 0.8,
              }}>{cfg.tag}</span>
              <span style={{ fontSize: 10, color: S.muted, letterSpacing: '0.04em' }}>{cfg.label}</span>
            </div>
            {/* Value */}
            <div style={{ fontSize: 22, fontWeight: 600, color: cfg.color, letterSpacing: '-0.02em', lineHeight: 1 }}>
              {cfg.format ? cfg.format(s.value) : formatMNT(s.value)}
            </div>
            {/* Meta */}
            <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${S.row}`, fontSize: 9, color: S.faint, letterSpacing: '0.05em' }}>
              {s.reference_date} · {s.source}
            </div>
          </div>
        );
      })}
    </div>
  );
}

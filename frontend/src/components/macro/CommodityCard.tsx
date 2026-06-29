import type { MacroIndicator } from '../../types/api';

interface Props {
  indicator: MacroIndicator;
  changePct: number | null;
}

interface CommodityMeta {
  name: string;
  unit: string;
  tag: string;
  prefix?: string;   // currency symbol, defaults to '$'
  isProxy?: boolean; // renders a PROXY badge
  subtitle?: string; // shown below the name
}

const COMMODITY_META: Record<string, CommodityMeta> = {
  COMMODITY_COPPER_USD_MT:  { name: 'Copper',          unit: '$/MT',      tag: 'CU' },
  COMMODITY_GOLD_USD_OZ:    { name: 'Gold',            unit: '$/OZ',      tag: 'AU' },
  COMMODITY_COAL_PROXY_HKD: {
    name: 'Yankuang Energy', unit: 'HKD/share', tag: 'YQ',
    prefix: 'HK$', isProxy: true, subtitle: '1171.HK · Coal Demand Proxy',
  },
};

const S = {
  border:   '#cbd6bb',
  surface:  '#f4f7f1',
  text:     '#1f2a18',
  muted:    '#5d6a52',
  faint:    '#8a977c',
  row:      '#e2e8da',
  up:       '#2f8f4e',
  down:     '#c4453b',
  neutral:  '#8a977c',
} as const;

function formatPrice(raw: string | null, prefix = '$', decimals = 0): string {
  if (raw == null) return '—';
  const n = parseFloat(raw);
  if (isNaN(n)) return '—';
  return prefix + n.toLocaleString(undefined, { maximumFractionDigits: decimals });
}

function formatChange(pct: number | null): { text: string; color: string } {
  if (pct == null) return { text: '—', color: S.neutral };
  const sign = pct > 0 ? '+' : '';
  const color = pct > 0 ? S.up : pct < 0 ? S.down : S.neutral;
  return { text: `${sign}${pct.toFixed(1)}%`, color };
}

function formatRefDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

export function CommodityCard({ indicator, changePct }: Props) {
  const meta = COMMODITY_META[indicator.indicator] ?? {
    name: indicator.indicator,
    unit: 'USD',
    tag: '—',
  };
  const { text: chgText, color: chgColor } = formatChange(changePct);

  return (
    <div style={{
      background: '#ffffff',
      border: `1px solid ${S.border}`,
      padding: '14px 16px',
      fontFamily: "'IBM Plex Mono', monospace",
      minWidth: 180,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: S.text, letterSpacing: '0.02em' }}>
            {meta.name}
          </div>
          {meta.subtitle ? (
            <div style={{ fontSize: 8, color: S.faint, marginTop: 2, letterSpacing: '0.05em' }}>
              {meta.subtitle}
            </div>
          ) : (
            <div style={{ fontSize: 9, color: S.faint, marginTop: 2, letterSpacing: '0.06em' }}>
              {meta.unit}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span style={{
            fontSize: 9, color: S.faint, letterSpacing: '0.06em',
            border: `1px solid ${S.row}`, padding: '2px 5px',
          }}>{meta.tag}</span>
          {meta.isProxy && (
            <span style={{
              fontSize: 7, fontWeight: 700, letterSpacing: '0.08em',
              color: '#b07d18', border: '1px solid #b07d18',
              padding: '1px 4px', opacity: 0.8,
            }}>PROXY</span>
          )}
        </div>
      </div>

      {/* Price */}
      <div style={{ fontSize: 20, fontWeight: 600, color: '#2b6cb0', letterSpacing: '-0.02em', lineHeight: 1 }}>
        {formatPrice(indicator.value, meta.prefix ?? '$', meta.isProxy ? 2 : 0)}
      </div>

      {/* MoM change */}
      <div style={{ marginTop: 6, fontSize: 10, fontWeight: 600, color: chgColor, letterSpacing: '0.02em' }}>
        {chgText} <span style={{ fontSize: 9, color: S.faint, fontWeight: 400 }}>MoM</span>
      </div>

      {/* Footer */}
      <div style={{
        marginTop: 10, paddingTop: 8,
        borderTop: `1px solid ${S.row}`,
        fontSize: 9, color: S.faint, letterSpacing: '0.05em',
      }}>
        {formatRefDate(indicator.reference_date)} · {indicator.source ?? '—'}
      </div>
    </div>
  );
}

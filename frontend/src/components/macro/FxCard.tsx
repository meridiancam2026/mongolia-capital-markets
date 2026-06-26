import type { MacroIndicator } from '../../types/api';

interface Props {
  indicator: MacroIndicator;
}

const CURRENCY_ISO: Record<string, string> = {
  USD: 'US Dollar',     EUR: 'Euro',           CNY: 'Chinese Yuan',
  JPY: 'Japanese Yen',  KRW: 'Korean Won',     RUB: 'Russian Ruble',
  GBP: 'British Pound', CHF: 'Swiss Franc',    AUD: 'Australian Dollar',
  HKD: 'Hong Kong Dollar', SGD: 'Singapore Dollar', CAD: 'Canadian Dollar',
  INR: 'Indian Rupee',  TRY: 'Turkish Lira',   MYR: 'Malaysian Ringgit',
};

function parsePair(code: string): { base: string; quote: string } {
  const stripped = code.replace(/^FX_/, '');
  const parts = stripped.split('_');
  return { base: parts[0] ?? code, quote: parts[1] ?? 'MNT' };
}

const S = {
  border:  '#cbd6bb',
  surface: '#f4f7f1',
  text:    '#1f2a18',
  muted:   '#5d6a52',
  faint:   '#8a977c',
  accent:  '#2b6cb0',
  row:     '#e2e8da',
} as const;

export function FxCard({ indicator }: Props) {
  const { base, quote } = parsePair(indicator.indicator);
  const rate = indicator.value != null
    ? parseFloat(indicator.value).toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 0 })
    : '—';
  const name = CURRENCY_ISO[base] ?? base;

  return (
    <div style={{
      background: '#ffffff',
      border: `1px solid ${S.border}`,
      padding: '14px 16px',
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: S.text, letterSpacing: '0.02em' }}>{base}</div>
          <div style={{ fontSize: 9, color: S.faint, marginTop: 2, letterSpacing: '0.06em' }}>{name}</div>
        </div>
        <span style={{
          fontSize: 9, color: S.faint, letterSpacing: '0.06em',
          border: `1px solid ${S.row}`, padding: '2px 5px',
        }}>{base}/{quote}</span>
      </div>

      {/* Rate */}
      <div style={{ fontSize: 20, fontWeight: 600, color: S.accent, letterSpacing: '-0.02em', lineHeight: 1 }}>
        ₮{rate}
      </div>

      {/* Footer */}
      <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${S.row}`, fontSize: 9, color: S.faint, letterSpacing: '0.05em' }}>
        {indicator.reference_date ?? '—'} · BOM
      </div>
    </div>
  );
}

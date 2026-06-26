import type { Quote } from '../../types/api';
import { formatMNT } from '../../utils/format';

interface Props {
  quotes: Quote[];
}

interface Stat {
  label: string;
  value: string | number;
  color: string;
  dot?: string;
}

export function SummaryStrip({ quotes }: Props) {
  let advancing = 0, declining = 0, unchanged = 0;
  let totalValue = 0;

  for (const q of quotes) {
    const c = q.change != null ? parseFloat(q.change) : 0;
    if (c > 0) advancing++;
    else if (c < 0) declining++;
    else unchanged++;
    if (q.value != null) totalValue += parseFloat(q.value);
  }

  const stats: Stat[] = [
    { label: 'ADVANCING', value: advancing,        color: '#2f8f4e', dot: '#2f8f4e' },
    { label: 'DECLINING', value: declining,        color: '#c4453b', dot: '#c4453b' },
    { label: 'UNCHANGED', value: unchanged,        color: '#8a977c' },
    { label: 'TOTAL VALUE',value: formatMNT(String(totalValue)), color: '#2b6cb0' },
    { label: 'SECURITIES', value: quotes.length,  color: '#5d6a52' },
  ];

  return (
    <div style={{
      display: 'flex', alignItems: 'stretch',
      background: '#ffffff',
      border: '1px solid #cbd6bb',
      marginBottom: 16,
      fontSize: 11,
    }}>
      {stats.map((s, i) => (
        <div
          key={s.label}
          style={{
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
            padding: '10px 18px',
            borderRight: i < stats.length - 1 ? '1px solid #e2e8da' : 'none',
            minWidth: 110,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {s.dot && (
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: s.dot, display: 'inline-block', flexShrink: 0 }} />
            )}
            <span style={{ fontSize: 15, fontWeight: 600, color: s.color, lineHeight: 1, letterSpacing: '-0.01em' }}>
              {s.value}
            </span>
          </div>
          <div style={{ fontSize: 8, color: '#8a977c', letterSpacing: '0.1em', marginTop: 3 }}>{s.label}</div>
        </div>
      ))}
    </div>
  );
}

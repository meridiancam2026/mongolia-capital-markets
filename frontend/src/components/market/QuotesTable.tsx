import { useState, useEffect } from 'react';
import type { Quote, Security } from '../../types/api';
import { formatChange, formatMNT, formatNumber, formatPct } from '../../utils/format';

type SortKey = 'ticker' | 'last' | 'change' | 'change_pct' | 'volume' | 'value';
type SortDir = 'asc' | 'desc';

interface Props {
  quotes: Quote[];
  securities?: Map<string, Security>;
  onSelectTicker: (ticker: string) => void;
}

function numVal(v: string | number | null | undefined): number {
  if (v == null) return -Infinity;
  return typeof v === 'string' ? parseFloat(v) : v;
}

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

const S = {
  text:    '#1f2a18',
  muted:   '#5d6a52',
  faint:   '#8a977c',
  border:  '#d3dcc6',
  row:     '#edf1e7',
  hover:   '#f1f5ec',
  up:      '#2f8f4e',
  down:    '#c4453b',
  accent:  '#2b6cb0',
  surface: '#f4f7f1',
} as const;

export function QuotesTable({ quotes, securities, onSelectTicker }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('value');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [flashTicker, setFlashTicker] = useState<string | null>(null);
  const [flashDir, setFlashDir] = useState<'up' | 'down'>('up');
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  useEffect(() => {
    if (quotes.length === 0) return;
    const id = setInterval(() => {
      const q = quotes[Math.floor(Math.random() * quotes.length)];
      const c = q.change != null ? parseFloat(q.change) : 0;
      setFlashTicker(q.ticker);
      setFlashDir(c >= 0 ? 'up' : 'down');
      const clear = setTimeout(() => setFlashTicker(null), 650);
      return () => clearTimeout(clear);
    }, 1400);
    return () => clearInterval(id);
  }, [quotes]);

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  }

  const sorted = [...quotes].sort((a, b) => {
    if (sortKey === 'ticker') {
      return sortDir === 'asc' ? a.ticker.localeCompare(b.ticker) : b.ticker.localeCompare(a.ticker);
    }
    const av = numVal(a[sortKey]), bv = numVal(b[sortKey]);
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  const thStyle = (k?: SortKey): React.CSSProperties => ({
    padding: '9px 10px',
    fontSize: 9,
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.09em',
    color: k && sortKey === k ? S.text : S.faint,
    cursor: k ? 'pointer' : 'default',
    userSelect: 'none',
    whiteSpace: 'nowrap',
    background: S.surface,
    borderBottom: `1px solid ${S.border}`,
  });

  return (
    <div style={{ border: `1px solid ${S.border}`, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', fontFamily: 'inherit' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle('ticker'), textAlign: 'left' }} onClick={() => handleSort('ticker')}>
                TICKER / COMPANY{sortKey === 'ticker' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle(), textAlign: 'right' }}>OPEN</th>
              <th style={{ ...thStyle(), textAlign: 'right' }}>HIGH</th>
              <th style={{ ...thStyle(), textAlign: 'right' }}>LOW</th>
              <th style={{ ...thStyle('last'), textAlign: 'right' }} onClick={() => handleSort('last')}>
                LAST{sortKey === 'last' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle('change'), textAlign: 'right' }} onClick={() => handleSort('change')}>
                CHG{sortKey === 'change' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle('change_pct'), textAlign: 'right' }} onClick={() => handleSort('change_pct')}>
                CHG%{sortKey === 'change_pct' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle('volume'), textAlign: 'right' }} onClick={() => handleSort('volume')}>
                VOL{sortKey === 'volume' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle('value'), textAlign: 'right' }} onClick={() => handleSort('value')}>
                VALUE{sortKey === 'value' ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
              <th style={{ ...thStyle(), textAlign: 'right' }}>TIME</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((q) => {
              const chg = q.change != null ? parseFloat(q.change) : 0;
              const chgColor = chg > 0 ? S.up : chg < 0 ? S.down : S.faint;
              const isFlashing = flashTicker === q.ticker;
              const isHovered = hoveredRow === q.ticker;

              let rowBg = '#ffffff';
              if (isFlashing) rowBg = flashDir === 'up' ? 'rgba(47,143,78,0.14)' : 'rgba(196,69,59,0.12)';
              else if (isHovered) rowBg = S.hover;

              const tdBase: React.CSSProperties = {
                padding: '7px 10px',
                borderBottom: `1px solid ${S.row}`,
                background: rowBg,
                transition: isFlashing ? 'none' : 'background 0.15s',
              };

              return (
                <tr
                  key={q.ticker}
                  onClick={() => onSelectTicker(q.ticker)}
                  onMouseEnter={() => setHoveredRow(q.ticker)}
                  onMouseLeave={() => setHoveredRow(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ ...tdBase, fontWeight: 600, color: S.accent, fontSize: 11 }}>
                    {(() => {
                      const sec = securities?.get(q.ticker);
                      const tooltip = [sec?.name, sec?.sector].filter(Boolean).join(' · ');
                      return (
                        <div title={tooltip || undefined} style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          <span>{q.ticker}</span>
                          {sec?.name && (
                            <span style={{ fontSize: 9, fontWeight: 400, color: S.muted, letterSpacing: '0.02em' }}>
                              {sec.name}
                            </span>
                          )}
                          {sec?.sector && (
                            <span style={{ fontSize: 8, fontWeight: 400, color: S.faint, letterSpacing: '0.02em' }}>
                              {sec.sector}
                            </span>
                          )}
                        </div>
                      );
                    })()}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.faint, fontSize: 10 }}>{formatNumber(q.open)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.faint, fontSize: 10 }}>{formatNumber(q.high)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.faint, fontSize: 10 }}>{formatNumber(q.low)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 500, color: S.text }}>{formatNumber(q.last)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', color: chgColor }}>{formatChange(q.change)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 500, color: chgColor }}>{formatPct(q.change_pct)}</td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.muted }}>
                    {q.volume != null ? q.volume.toLocaleString() : '—'}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 600, color: S.accent }}>
                    {formatMNT(q.value)}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontSize: 10, color: S.faint }}>
                    {fmtTime(q.trade_time)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

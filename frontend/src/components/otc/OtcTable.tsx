import { useState } from 'react';
import type { OtcTrade } from '../../types/api';
import { formatMNT, formatNumber } from '../../utils/format';

interface Props {
  trades: OtcTrade[];
}

const S = {
  text:    '#1f2a18',
  muted:   '#5d6a52',
  faint:   '#8a977c',
  border:  '#d3dcc6',
  row:     '#edf1e7',
  hover:   '#f1f5ec',
  accent:  '#2b6cb0',
  amber:   '#b07d18',
  surface: '#f4f7f1',
} as const;

export function OtcTable({ trades }: Props) {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  if (trades.length === 0) {
    return (
      <div style={{
        background: '#ffffff', border: `1px solid ${S.border}`,
        padding: '32px', textAlign: 'center',
        fontSize: 11, color: S.faint, fontFamily: 'inherit',
        letterSpacing: '0.06em',
      }}>
        NO OTC BOND DATA AVAILABLE
      </div>
    );
  }

  const thStyle: React.CSSProperties = {
    padding: '9px 12px',
    fontSize: 9, fontWeight: 600,
    textTransform: 'uppercase', letterSpacing: '0.09em',
    color: S.faint,
    background: S.surface,
    borderBottom: `1px solid ${S.border}`,
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ border: `1px solid ${S.border}`, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', fontFamily: 'inherit' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, textAlign: 'left' }}>BOND</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>PRICE</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>YIELD</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>VOLUME</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>VALUE</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>DATE</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => {
              const yld = t['yield'];
              const isHovered = hoveredRow === t.id;
              const tdBase: React.CSSProperties = {
                padding: '10px 12px',
                borderBottom: `1px solid ${S.row}`,
                background: isHovered ? S.hover : '#ffffff',
                transition: 'background 0.12s',
              };
              return (
                <tr
                  key={t.id}
                  onMouseEnter={() => setHoveredRow(t.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  <td style={{ ...tdBase }}>
                    <div style={{ fontWeight: 600, color: S.text, fontFamily: "'Inter Tight', sans-serif", fontSize: 12 }}>
                      {t.bond_name}
                    </div>
                    {t.market_type && (
                      <div style={{ fontSize: 8, color: S.faint, marginTop: 2, letterSpacing: '0.08em' }}>
                        {t.market_type.toUpperCase()}
                      </div>
                    )}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.muted }}>
                    {t.price != null ? formatNumber(t.price) : '—'}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 600, color: S.amber }}>
                    {yld != null ? `${parseFloat(yld).toFixed(2)}%` : '—'}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', color: S.muted }}>
                    {t.volume != null ? t.volume.toLocaleString() : '—'}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 600, color: S.accent }}>
                    {formatMNT(t.value)}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontSize: 10, color: S.faint }}>
                    {t.trade_date}
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

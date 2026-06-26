import { useState } from 'react';
import type { RegulatoryIndicator } from '../../types/api';
import { formatMNT, formatNumber } from '../../utils/format';

interface Props {
  stats: RegulatoryIndicator[];
}

function formatValue(stat: RegulatoryIndicator): string {
  if (stat.value == null) return '—';
  const unit = (stat.unit ?? '').toLowerCase();
  if (unit === '%' || unit === 'percent') return `${parseFloat(stat.value).toFixed(2)}%`;
  if (unit === 'mnt') return formatMNT(stat.value);
  if (unit === 'count') return formatNumber(stat.value);
  return stat.value;
}

function sourceBadge(indicator: string): { label: string; color: string; bg: string } {
  const i = indicator.toLowerCase();
  if (i.includes('policy') || i.includes('bom') || i.includes('rate'))
    return { label: 'BOM', color: '#2b6cb0', bg: 'rgba(43,108,176,0.08)' };
  if (i.includes('frc') || i.includes('broker') || i.includes('fund') || i.includes('regul'))
    return { label: 'FRC', color: '#b07d18', bg: 'rgba(176,125,24,0.08)' };
  return { label: 'MASD', color: '#2f8f4e', bg: 'rgba(47,143,78,0.08)' };
}

function formatIndicatorLabel(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

const S = {
  text:    '#1f2a18',
  muted:   '#5d6a52',
  faint:   '#8a977c',
  border:  '#d3dcc6',
  row:     '#edf1e7',
  hover:   '#f1f5ec',
  accent:  '#2b6cb0',
  surface: '#f4f7f1',
} as const;

export function RegulatoryTable({ stats }: Props) {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const thStyle: React.CSSProperties = {
    padding: '9px 12px',
    fontSize: 9, fontWeight: 600,
    textTransform: 'uppercase', letterSpacing: '0.09em',
    color: S.faint, background: S.surface,
    borderBottom: `1px solid ${S.border}`,
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ border: `1px solid ${S.border}`, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', fontFamily: 'inherit' }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, textAlign: 'left' }}>INDICATOR</th>
              <th style={{ ...thStyle, textAlign: 'left' }}>SOURCE</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>VALUE</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>YEAR</th>
            </tr>
          </thead>
          <tbody>
            {stats.map((s) => {
              const badge = sourceBadge(s.indicator);
              const isHovered = hoveredRow === s.id;
              const tdBase: React.CSSProperties = {
                padding: '10px 12px',
                borderBottom: `1px solid ${S.row}`,
                background: isHovered ? S.hover : '#ffffff',
                transition: 'background 0.12s',
              };
              return (
                <tr
                  key={s.id}
                  onMouseEnter={() => setHoveredRow(s.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  <td style={{ ...tdBase }}>
                    <span style={{ fontFamily: "'Inter Tight', sans-serif", color: S.text, fontSize: 12 }}>
                      {formatIndicatorLabel(s.indicator)}
                    </span>
                  </td>
                  <td style={{ ...tdBase }}>
                    <span style={{
                      display: 'inline-block',
                      fontSize: 8, fontWeight: 700, letterSpacing: '0.1em',
                      color: badge.color, background: badge.bg,
                      border: `1px solid ${badge.color}`,
                      padding: '2px 6px', opacity: 0.9,
                    }}>{badge.label}</span>
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontWeight: 600, color: S.accent }}>
                    {formatValue(s)}
                  </td>
                  <td style={{ ...tdBase, textAlign: 'right', fontSize: 10, color: S.faint }}>
                    {s.reference_year}
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

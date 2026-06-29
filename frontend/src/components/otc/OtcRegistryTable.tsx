import { useState, useMemo } from 'react';
import type { OtcBondRegistry } from '../../types/api';

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
  green:   '#276749',
} as const;

const BOARD_COLOR: Record<string, string> = {
  A: '#276749',
  B: '#2b6cb0',
  C: '#b07d18',
};

interface Props {
  bonds: OtcBondRegistry[];
}

export function OtcRegistryTable({ bonds }: Props) {
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('ALL');
  const [board, setBoard] = useState('ALL');
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const sectors = useMemo(() => {
    const s = new Set(bonds.map(b => b.sector).filter(Boolean) as string[]);
    return ['ALL', ...Array.from(s).sort()];
  }, [bonds]);

  const boards = useMemo(() => {
    const b = new Set(bonds.map(b => b.board_category).filter(Boolean) as string[]);
    return ['ALL', ...Array.from(b).sort()];
  }, [bonds]);

  const filtered = useMemo(() => bonds.filter(b => {
    if (board !== 'ALL' && b.board_category !== board) return false;
    if (sector !== 'ALL' && b.sector !== sector) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        b.bond_name.toLowerCase().includes(q) ||
        (b.underwriter ?? '').toLowerCase().includes(q)
      );
    }
    return true;
  }), [bonds, search, sector, board]);

  const thStyle: React.CSSProperties = {
    padding: '9px 12px',
    fontSize: 9, fontWeight: 600,
    textTransform: 'uppercase', letterSpacing: '0.09em',
    color: S.faint, background: S.surface,
    borderBottom: `1px solid ${S.border}`,
    whiteSpace: 'nowrap',
  };

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search bond or underwriter…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            flex: 1, minWidth: 160, padding: '6px 10px',
            fontSize: 11, border: `1px solid ${S.border}`,
            background: '#fff', color: S.text, outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <select
          value={board}
          onChange={e => setBoard(e.target.value)}
          style={{
            padding: '6px 10px', fontSize: 11,
            border: `1px solid ${S.border}`, background: '#fff',
            color: S.text, fontFamily: 'inherit',
          }}
        >
          {boards.map(b => <option key={b} value={b}>{b === 'ALL' ? 'All Boards' : `Board ${b}`}</option>)}
        </select>
        <select
          value={sector}
          onChange={e => setSector(e.target.value)}
          style={{
            padding: '6px 10px', fontSize: 11,
            border: `1px solid ${S.border}`, background: '#fff',
            color: S.text, fontFamily: 'inherit',
          }}
        >
          {sectors.map(s => <option key={s} value={s}>{s === 'ALL' ? 'All Sectors' : s}</option>)}
        </select>
        <div style={{ fontSize: 10, color: S.faint, alignSelf: 'center', whiteSpace: 'nowrap' }}>
          {filtered.length} / {bonds.length} bonds
        </div>
      </div>

      {/* Table */}
      <div style={{ border: `1px solid ${S.border}`, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto', maxHeight: 480, overflowY: 'auto' }}>
          <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', fontFamily: 'inherit' }}>
            <thead style={{ position: 'sticky', top: 0, zIndex: 1 }}>
              <tr>
                <th style={{ ...thStyle, textAlign: 'center', width: 48 }}>BRD</th>
                <th style={{ ...thStyle, textAlign: 'left' }}>BOND</th>
                <th style={{ ...thStyle, textAlign: 'left' }}>SECTOR</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>COUPON</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>TERM</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>CCY</th>
                <th style={{ ...thStyle, textAlign: 'left' }}>UNDERWRITER</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>ISSUED</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((b) => {
                const isHovered = hoveredRow === b.id;
                const tdBase: React.CSSProperties = {
                  padding: '9px 12px',
                  borderBottom: `1px solid ${S.row}`,
                  background: isHovered ? S.hover : '#ffffff',
                  transition: 'background 0.1s',
                };
                const boardColor = b.board_category ? BOARD_COLOR[b.board_category] ?? S.muted : S.muted;
                return (
                  <tr
                    key={b.id}
                    onMouseEnter={() => setHoveredRow(b.id)}
                    onMouseLeave={() => setHoveredRow(null)}
                  >
                    <td style={{ ...tdBase, textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-block', padding: '1px 6px',
                        fontSize: 9, fontWeight: 700, letterSpacing: '0.05em',
                        color: boardColor, border: `1px solid ${boardColor}`,
                      }}>
                        {b.board_category ?? '—'}
                      </span>
                    </td>
                    <td style={{ ...tdBase }}>
                      <div style={{ fontWeight: 600, color: S.text, fontSize: 11 }}>
                        {b.bond_name}
                      </div>
                    </td>
                    <td style={{ ...tdBase, color: S.muted, fontSize: 10 }}>
                      {b.sector ?? '—'}
                    </td>
                    <td style={{ ...tdBase, textAlign: 'right', fontWeight: 600, color: S.amber }}>
                      {b.coupon_rate_raw ?? '—'}
                    </td>
                    <td style={{ ...tdBase, textAlign: 'right', color: S.muted }}>
                      {b.maturity_months != null ? `${b.maturity_months}m` : '—'}
                    </td>
                    <td style={{ ...tdBase, textAlign: 'right', color: S.muted, fontSize: 10 }}>
                      {b.currency ?? '—'}
                    </td>
                    <td style={{ ...tdBase, color: S.muted, fontSize: 10 }}>
                      {b.underwriter ?? '—'}
                    </td>
                    <td style={{ ...tdBase, textAlign: 'right', fontSize: 10, color: S.faint }}>
                      {b.issue_date ?? '—'}
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: 32, textAlign: 'center', color: S.faint, fontSize: 11 }}>
                    NO BONDS MATCH FILTER
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

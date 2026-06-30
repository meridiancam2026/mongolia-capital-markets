import { useState, useEffect } from 'react';
import { MarketView } from './views/MarketView';
import { LocalBondsView } from './views/LocalBondsView';
import { EurobondsView } from './views/EurobondsView';
import { MacroView } from './views/MacroView';
import { RegulatoryView } from './views/RegulatoryView';
import { CommoditiesView } from './views/CommoditiesView';

type Tab = 'market' | 'local-bonds' | 'eurobonds' | 'macro' | 'regulatory' | 'commodities';

const TABS: { id: Tab; label: string; short: string }[] = [
  { id: 'market',      label: 'Equities',     short: 'EQ'  },
  { id: 'local-bonds', label: 'Local Bonds',  short: 'LCL' },
  { id: 'eurobonds',   label: 'Eurobonds',    short: 'EUR' },
  { id: 'macro',       label: 'Macro',        short: 'MCR' },
  { id: 'regulatory',  label: 'Regulatory',   short: 'REG' },
  { id: 'commodities', label: 'Commodities',  short: 'CMD' },
];

const S = {
  bg:       '#e6ede1',
  sidebar:  '#eef2ea',
  surface:  '#f4f7f1',
  text:     '#1f2a18',
  muted:    '#5d6a52',
  faint:    '#8a977c',
  border:   '#d3dcc6',
  up:       '#2f8f4e',
} as const;

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('market');
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const timeStr = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const dateStr = now.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: '2-digit' });

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden', fontFamily: "'IBM Plex Mono', monospace" }}>

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside style={{
        width: 222, minWidth: 222,
        background: S.sidebar,
        borderRight: `1px solid ${S.border}`,
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{ padding: '18px 16px 14px', borderBottom: `1px solid ${S.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: S.text, letterSpacing: '-0.01em' }}>
              MSE TERMINAL
            </span>
            <span
              className="led-sidebar"
              style={{ width: 6, height: 6, borderRadius: '50%', background: S.up, marginLeft: 'auto', flexShrink: 0 }}
            />
          </div>
          <div style={{ fontSize: 9, color: S.faint, marginTop: 5, letterSpacing: '0.08em' }}>
            MONGOLIA CAPITAL MARKETS
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '10px 8px' }}>
          {TABS.map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  width: '100%', padding: '9px 10px',
                  border: 'none', borderLeft: active ? `2px solid ${S.up}` : '2px solid transparent',
                  cursor: 'pointer', textAlign: 'left',
                  fontSize: 11, fontWeight: active ? 600 : 400, letterSpacing: '0.03em',
                  color: active ? S.text : S.muted,
                  background: active ? S.surface : 'transparent',
                  marginBottom: 2, fontFamily: 'inherit',
                  transition: 'background 0.12s',
                }}
              >
                <span style={{ fontSize: 9, letterSpacing: '0.1em', color: S.faint, width: 26 }}>
                  {tab.short}
                </span>
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Sidebar footer */}
        <div style={{ borderTop: `1px solid ${S.border}`, padding: '10px 16px' }}>
          <div style={{ fontSize: 9, color: S.faint, letterSpacing: '0.06em' }}>MSE · MASD · BOM · FRC</div>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: S.bg }}>

        {/* Header */}
        <header style={{
          height: 52, minHeight: 52,
          background: S.surface, borderBottom: `1px solid ${S.border}`,
          display: 'flex', alignItems: 'center',
          padding: '0 24px', gap: 16, justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: S.text, letterSpacing: '0.05em' }}>
              {TABS.find(t => t.id === activeTab)?.label.toUpperCase()}
            </span>
            <span style={{ fontSize: 10, color: S.faint }}>Mongolian Stock Exchange</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                className="led-header"
                style={{ width: 5, height: 5, borderRadius: '50%', background: S.up, display: 'inline-block' }}
              />
              <span style={{ fontSize: 9, color: S.muted, letterSpacing: '0.1em' }}>LIVE</span>
            </div>
            <span style={{ fontSize: 11, color: S.muted, fontVariantNumeric: 'tabular-nums' }}>{timeStr}</span>
            <span style={{ fontSize: 10, color: S.faint }}>{dateStr}</span>
          </div>
        </header>

        {/* Content — display:none preserves mount & hook state across tabs */}
        <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          {(['market', 'local-bonds', 'eurobonds', 'macro', 'regulatory', 'commodities'] as const).map((tab) => (
            <div
              key={tab}
              style={{
                display: activeTab === tab ? 'block' : 'none',
                height: '100%', overflow: 'auto',
                padding: '22px 24px',
              }}
            >
              {tab === 'market'      && <MarketView />}
              {tab === 'local-bonds' && <LocalBondsView />}
              {tab === 'eurobonds'   && <EurobondsView />}
              {tab === 'macro'       && <MacroView />}
              {tab === 'regulatory'  && <RegulatoryView />}
              {tab === 'commodities' && <CommoditiesView />}
            </div>
          ))}
        </div>

        {/* Footer */}
        <footer style={{
          height: 30, minHeight: 30,
          background: S.sidebar, borderTop: `1px solid ${S.border}`,
          display: 'flex', alignItems: 'center',
          padding: '0 24px', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: 9, color: S.faint, letterSpacing: '0.06em' }}>
            MONGOLIAN STOCK EXCHANGE TERMINAL
          </span>
          <span style={{ fontSize: 9, color: S.faint, letterSpacing: '0.04em' }}>
            60s REFRESH · MSE / MASD / BOM / FRC
          </span>
        </footer>
      </div>
    </div>
  );
}

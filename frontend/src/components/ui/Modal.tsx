import { useEffect } from 'react';

interface Props {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function Modal({ title, onClose, children }: Props) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 50,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <div
        onClick={onClose}
        style={{ position: 'absolute', inset: 0, background: 'rgba(31,42,24,0.55)', backdropFilter: 'blur(2px)' }}
      />
      <div style={{
        position: 'relative',
        background: '#f4f7f1',
        border: '1px solid #cbd6bb',
        width: '100%', maxWidth: 820,
        maxHeight: '88vh', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        fontFamily: "'IBM Plex Mono', monospace",
      }}>
        {/* Modal header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 18px',
          borderBottom: '1px solid #d3dcc6',
          background: '#eef2ea',
        }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#1f2a18', letterSpacing: '0.04em' }}>
            {title.toUpperCase()}
          </span>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: '1px solid #d3dcc6',
              cursor: 'pointer', fontSize: 13,
              color: '#8a977c', width: 24, height: 24,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'inherit',
            }}
          >
            ×
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {children}
        </div>
      </div>
    </div>
  );
}

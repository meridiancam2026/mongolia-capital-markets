export function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0', gap: 10 }}>
      <span style={{ fontSize: 10, color: '#8a977c', letterSpacing: '0.1em', animation: 'mcm-led 1.2s ease-in-out infinite' }}>
        LOADING
      </span>
      <span style={{ display: 'inline-block', width: 5, height: 5, borderRadius: '50%', background: '#2f8f4e', animation: 'mcm-led 1.2s ease-in-out infinite' }} />
    </div>
  );
}

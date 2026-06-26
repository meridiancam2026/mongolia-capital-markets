interface Props {
  message: string;
}

export function ErrorBanner({ message }: Props) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      borderLeft: '3px solid #c4453b',
      background: 'rgba(196,69,59,0.06)',
      padding: '10px 14px', marginBottom: 16,
      fontSize: 11, color: '#c4453b', fontFamily: 'inherit',
    }}>
      <span style={{ fontWeight: 600, letterSpacing: '0.06em' }}>ERR</span>
      <span style={{ color: '#5d6a52' }}>{message}</span>
    </div>
  );
}

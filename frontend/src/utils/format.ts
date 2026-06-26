export function formatMNT(raw: string | number | null | undefined): string {
  if (raw == null || raw === '') return '—';
  const n = typeof raw === 'string' ? parseFloat(raw) : raw;
  if (!isFinite(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e9) return `₮${(n / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `₮${(n / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `₮${(n / 1e3).toFixed(1)}K`;
  return `₮${n.toLocaleString()}`;
}

export function formatNumber(raw: string | number | null | undefined): string {
  if (raw == null || raw === '') return '—';
  const n = typeof raw === 'string' ? parseFloat(raw) : raw;
  if (!isFinite(n)) return '—';
  return n.toLocaleString();
}

export function formatChange(raw: string | null | undefined): string {
  if (raw == null || raw === '') return '—';
  const n = parseFloat(raw);
  if (!isFinite(n)) return '—';
  return n > 0 ? `+${n.toFixed(2)}` : n.toFixed(2);
}

export function formatPct(raw: string | null | undefined): string {
  if (raw == null || raw === '') return '—';
  const n = parseFloat(raw);
  if (!isFinite(n)) return '—';
  return n > 0 ? `+${n.toFixed(2)}%` : `${n.toFixed(2)}%`;
}

export function changeColorClass(raw: string | null | undefined): string {
  if (raw == null || raw === '') return 'text-gray-400';
  const n = parseFloat(raw);
  if (n > 0) return 'text-green-500';
  if (n < 0) return 'text-red-500';
  return 'text-gray-400';
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return iso.split('T')[0];
}

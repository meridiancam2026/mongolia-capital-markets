import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { EquityHistory } from '../types/api';

interface UseEquityHistoryResult {
  data: EquityHistory[];
  loading: boolean;
  error: string | null;
}

export function useEquityHistory(ticker: string | null): UseEquityHistoryResult {
  const [data, setData] = useState<EquityHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setData([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    apiFetch<EquityHistory[]>(`/api/quotes/${encodeURIComponent(ticker)}/history`)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setError(e instanceof ApiError ? e.message : 'Network error'); setLoading(false); } });
    return () => { cancelled = true; };
  }, [ticker]);

  return { data, loading, error };
}

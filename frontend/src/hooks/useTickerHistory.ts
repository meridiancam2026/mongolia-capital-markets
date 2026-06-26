import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { Quote } from '../types/api';

interface UseTickerHistoryResult {
  data: Quote[];
  loading: boolean;
  error: string | null;
}

export function useTickerHistory(ticker: string | null): UseTickerHistoryResult {
  const [data, setData] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setData([]);
      return;
    }
    setLoading(true);
    setError(null);
    apiFetch<Quote[]>(`/api/quotes/${ticker}?limit=100`)
      .then((d) => setData(d))
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, [ticker]);

  return { data, loading, error };
}

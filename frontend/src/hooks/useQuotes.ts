import { useCallback, useEffect, useState } from 'react';
import { apiFetch, apiPost, pollUntilChanged, ApiError } from '../api/client';
import type { Quote } from '../types/api';

interface UseQuotesResult {
  data: Quote[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

export function useQuotes(): UseQuotesResult {
  const [data, setData] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const doFetch = useCallback(async (background = false) => {
    if (!background) setLoading(true);
    try {
      const quotes = await apiFetch<Quote[]>('/api/quotes');
      setData(quotes);
      setError(null);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Network error');
    } finally {
      if (!background) setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    const snapshot = data[0]?.trade_time ?? null;
    try {
      await apiPost('/api/admin/trigger/ingest_mse');
    } catch { /* non-fatal */ }
    // Poll every 10s until trade_time changes (workflow completes in ~30-60s with cache)
    const fresh = await pollUntilChanged(
      () => apiFetch<Quote[]>('/api/quotes'),
      (rows) => (rows[0]?.trade_time ?? null) !== snapshot,
    );
    if (fresh) {
      setData(fresh);
      setLastUpdated(new Date());
    } else {
      await doFetch(false);
    }
    setRefreshing(false);
  }, [doFetch, data]);

  useEffect(() => {
    doFetch(false);
    const id = setInterval(() => doFetch(true), 60_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { data, loading, refreshing, error, lastUpdated, refresh };
}

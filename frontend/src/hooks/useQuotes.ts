import { useCallback, useEffect, useState } from 'react';
import { apiFetch, apiPost, ApiError } from '../api/client';
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
    try {
      // Fire workflow dispatch (async — completes in ~2 min in background)
      await apiPost('/api/admin/trigger/ingest_mse');
    } catch {
      // Non-fatal: workflow trigger failing shouldn't block the DB re-fetch
    }
    await doFetch(false);
    setRefreshing(false);
  }, [doFetch]);

  useEffect(() => {
    doFetch(false);
    const id = setInterval(() => doFetch(true), 60_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { data, loading, refreshing, error, lastUpdated, refresh };
}

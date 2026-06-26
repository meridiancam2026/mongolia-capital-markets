import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { Quote } from '../types/api';

interface UseQuotesResult {
  data: Quote[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useQuotes(): UseQuotesResult {
  const [data, setData] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    doFetch(false);
    const id = setInterval(() => doFetch(true), 60_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { data, loading, error, lastUpdated };
}

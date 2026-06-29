import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { MacroIndicator } from '../types/api';

export function useCommodities() {
  const [data, setData] = useState<MacroIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const doFetch = useCallback(async (background = false) => {
    if (!background) setLoading(true);
    try {
      const d = await apiFetch<MacroIndicator[]>('/api/macro/commodities');
      setData(d);
      setError(null);
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

  return { data, loading, error };
}

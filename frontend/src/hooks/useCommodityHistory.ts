import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { MacroIndicator } from '../types/api';

export function useCommodityHistory(indicator: string) {
  const [data, setData] = useState<MacroIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!indicator) return;
    setLoading(true);
    setError(null);
    apiFetch<MacroIndicator[]>(`/api/macro/commodities/history/${indicator}`)
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, [indicator]);

  return { data, loading, error };
}

import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { OtcTrade } from '../types/api';

export function useOtc(segment?: 'local' | 'eurobond') {
  const [data, setData] = useState<OtcTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const url = segment ? `/api/otc?segment=${segment}` : '/api/otc';

  useEffect(() => {
    apiFetch<OtcTrade[]>(url)
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, [url, tick]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { data, loading, error, refetch };
}

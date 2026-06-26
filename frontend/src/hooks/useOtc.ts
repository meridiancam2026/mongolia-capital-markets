import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { OtcTrade } from '../types/api';

export function useOtc() {
  const [data, setData] = useState<OtcTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<OtcTrade[]>('/api/otc')
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

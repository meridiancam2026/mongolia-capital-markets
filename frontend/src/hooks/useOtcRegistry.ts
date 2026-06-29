import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { OtcBondRegistry } from '../types/api';

export function useOtcRegistry() {
  const [data, setData] = useState<OtcBondRegistry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<OtcBondRegistry[]>('/api/otc/registry')
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

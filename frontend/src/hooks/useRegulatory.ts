import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { RegulatoryIndicator } from '../types/api';

export function useRegulatory() {
  const [data, setData] = useState<RegulatoryIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<RegulatoryIndicator[]>('/api/regulatory')
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

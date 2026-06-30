import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { BondPriceHistory } from '../types/api';

export function useBondHistory(bondName: string | null) {
  const [data, setData] = useState<BondPriceHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bondName) {
      setData([]);
      return;
    }
    setLoading(true);
    setError(null);
    apiFetch<BondPriceHistory[]>(`/api/bonds/history?bond_name=${encodeURIComponent(bondName)}`)
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, [bondName]);

  return { data, loading, error };
}

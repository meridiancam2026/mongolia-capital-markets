import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { MacroIndicator } from '../types/api';

export function useMacro() {
  const [data, setData] = useState<MacroIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<MacroIndicator[]>('/api/macro')
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Network error'))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

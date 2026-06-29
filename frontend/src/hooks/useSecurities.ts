import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client';
import type { Security } from '../types/api';

export function useSecurities(): Map<string, Security> {
  const [map, setMap] = useState<Map<string, Security>>(new Map());

  useEffect(() => {
    apiFetch<Security[]>('/api/securities')
      .then((list) => setMap(new Map(list.map((s) => [s.ticker, s]))))
      .catch((e) => {
        if (e instanceof ApiError) console.warn('Securities fetch failed:', e.message);
      });
  }, []);

  return map;
}

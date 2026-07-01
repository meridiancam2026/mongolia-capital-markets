const BASE = import.meta.env.VITE_API_URL ?? '';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' });
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${res.statusText}`);
  }
}

/** Poll `fetch` every `intervalMs` until `hasChanged` returns true or `maxAttempts` exceeded. */
export async function pollUntilChanged<T>(
  fetch: () => Promise<T>,
  hasChanged: (data: T) => boolean,
  intervalMs = 10_000,
  maxAttempts = 9,
): Promise<T | null> {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise<void>((r) => setTimeout(r, intervalMs));
    try {
      const data = await fetch();
      if (hasChanged(data)) return data;
    } catch { /* keep polling */ }
  }
  return null;
}

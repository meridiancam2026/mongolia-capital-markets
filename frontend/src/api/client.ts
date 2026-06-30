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

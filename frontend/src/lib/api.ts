const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export function getApiUrl(endpoint: string): string {
  return endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
}

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = getApiUrl(endpoint);
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

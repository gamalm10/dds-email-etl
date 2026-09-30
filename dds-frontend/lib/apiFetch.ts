import { useAuthStore } from '@/stores/authStore';

/**
 * Exchange the stored refresh token for a new access token.
 *
 * The chat used a bare fetch, which skipped the axios interceptor and so
 * surfaced a raw 401 as soon as the 1 hour access token expired. Both paths
 * now call this so there is a single refresh implementation.
 *
 * Returns the new access token, or null if the session cannot be recovered.
 */
export async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;

  const store = useAuthStore.getState();
  if (!store.refreshToken) return null;

  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: store.refreshToken }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    if (!data?.accessToken) return null;

    store.setTokens(data.accessToken, data.refreshToken || store.refreshToken);
    return data.accessToken as string;
  } catch {
    return null;
  }
}

export function redirectToLogin(): void {
  if (typeof window === 'undefined') return;
  useAuthStore.getState().logout();
  window.location.href = '/login?expired=true';
}

/** fetch that authenticates with the stored token and transparently refreshes once on 401. */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const token = useAuthStore.getState().accessToken;

  const buildHeaders = (bearer?: string | null): Headers => {
    const headers = new Headers(init.headers);
    headers.set('Content-Type', 'application/json');
    if (bearer) headers.set('Authorization', `Bearer ${bearer}`);
    return headers;
  };

  let res = await fetch(url, { ...init, headers: buildHeaders(token) });

  if (res.status !== 401) return res;

  const fresh = await refreshAccessToken();
  if (!fresh) {
    redirectToLogin();
    return res;
  }

  return fetch(url, { ...init, headers: buildHeaders(fresh) });
}

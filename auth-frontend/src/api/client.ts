import { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void): void {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed(token: string): void {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function onRefreshFailed(): void {
  refreshSubscribers = [];
}

function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

function setAccessToken(token: string): void {
  localStorage.setItem('access_token', token);
}

function clearAccessToken(): void {
  localStorage.removeItem('access_token');
}

async function attemptRefresh(): Promise<string> {
  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    clearAccessToken();
    throw new ApiError(401, 'REFRESH_FAILED', 'Session expired. Please log in again.');
  }

  const data = await response.json();
  const newToken: string = data.access_token;
  setAccessToken(newToken);
  return newToken;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (response.status === 401 && retry) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const newToken = await attemptRefresh();
        isRefreshing = false;
        onTokenRefreshed(newToken);
      } catch (err) {
        isRefreshing = false;
        onRefreshFailed();
        throw err;
      }
    }

    return new Promise<T>((resolve, reject) => {
      subscribeTokenRefresh((newToken) => {
        const retryHeaders: Record<string, string> = {
          ...headers,
          Authorization: `Bearer ${newToken}`,
        };
        fetch(`${BASE_URL}${path}`, {
          ...options,
          credentials: 'include',
          headers: retryHeaders,
        })
          .then(async (retryResponse) => {
            if (!retryResponse.ok) {
              const body = await retryResponse.json().catch(() => ({}));
              const err = body?.error ?? {};
              reject(
                new ApiError(
                  retryResponse.status,
                  err.code ?? 'UNKNOWN_ERROR',
                  err.message ?? 'An unexpected error occurred.',
                  err.details,
                ),
              );
              return;
            }
            const data: T = await retryResponse.json().catch(() => ({} as T));
            resolve(data);
          })
          .catch(reject);
      });
    });
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const err = body?.error ?? {};
    throw new ApiError(
      response.status,
      err.code ?? 'UNKNOWN_ERROR',
      err.message ?? 'An unexpected error occurred.',
      err.details,
    );
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export { getAccessToken, setAccessToken, clearAccessToken };

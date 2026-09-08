const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
}

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface RegisterResponse {
  accessToken: string;
  tokenType: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LogoutResponse {
  message: string;
}

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const accessToken = sessionStorage.getItem('accessToken') ?? localStorage.getItem('accessToken');
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let message = 'Invalid email or password.';
    let code: string | undefined;
    try {
      const data = await response.json();
      if (data?.error?.message) {
        message = data.error.message;
      }
      if (data?.error?.code) {
        code = data.error.code;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(message, response.status, code);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

function toSnakeCase(body: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(body)) {
    const snakeKey = key.replace(/([A-Z])/g, (char) => `_${char.toLowerCase()}`);
    result[snakeKey] = value;
  }
  return result;
}

function fromSnakeCase(body: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(body)) {
    const camelKey = key.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase());
    result[camelKey] = value;
  }
  return result;
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const body = toSnakeCase(payload as unknown as Record<string, unknown>);
  const raw = await request<Record<string, unknown>>('POST', '/auth/login', body);
  const data = fromSnakeCase(raw) as unknown as LoginResponse;

  const storage = payload.rememberMe ? localStorage : sessionStorage;
  storage.setItem('accessToken', data.accessToken);

  return data;
}

export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  const body = toSnakeCase(payload as unknown as Record<string, unknown>);
  const raw = await request<Record<string, unknown>>('POST', '/auth/register', body);
  const data = fromSnakeCase(raw) as unknown as RegisterResponse;

  sessionStorage.setItem('accessToken', data.accessToken);

  return data;
}

export async function forgotPassword(payload: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
  const body = toSnakeCase(payload as unknown as Record<string, unknown>);
  const raw = await request<Record<string, unknown>>('POST', '/auth/forgot-password', body);
  return fromSnakeCase(raw) as unknown as ForgotPasswordResponse;
}

export async function resetPassword(payload: ResetPasswordRequest): Promise<ResetPasswordResponse> {
  const body = toSnakeCase(payload as unknown as Record<string, unknown>);
  const raw = await request<Record<string, unknown>>('POST', '/auth/reset-password', body);
  return fromSnakeCase(raw) as unknown as ResetPasswordResponse;
}

export async function me(): Promise<MeResponse> {
  const raw = await request<Record<string, unknown>>('GET', '/auth/me');
  return fromSnakeCase(raw) as unknown as MeResponse;
}

export async function logout(): Promise<LogoutResponse> {
  const raw = await request<Record<string, unknown>>('POST', '/auth/logout');
  localStorage.removeItem('accessToken');
  sessionStorage.removeItem('accessToken');
  return fromSnakeCase(raw) as unknown as LogoutResponse;
}

export async function refresh(): Promise<RefreshResponse> {
  const raw = await request<Record<string, unknown>>('POST', '/auth/refresh');
  const data = fromSnakeCase(raw) as unknown as RefreshResponse;

  const hadLocal = localStorage.getItem('accessToken') !== null;
  const storage = hadLocal ? localStorage : sessionStorage;
  storage.setItem('accessToken', data.accessToken);

  return data;
}

export { ApiError };

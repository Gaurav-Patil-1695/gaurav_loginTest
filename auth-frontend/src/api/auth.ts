const API_BASE = '/auth';

export interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface RegisterResponse {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirm_password: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorPayload: unknown;
    try {
      errorPayload = await response.json();
    } catch {
      errorPayload = { error: { code: 'UNKNOWN', message: response.statusText } };
    }
    throw errorPayload;
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('POST', '/login', data);
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('POST', '/register', data);
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  return request<void>('POST', '/forgot-password', data);
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  return request<void>('POST', '/reset-password', data);
}

export async function me(): Promise<UserProfile> {
  return request<UserProfile>('GET', '/me');
}

export async function logout(): Promise<void> {
  return request<void>('POST', '/logout');
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('POST', '/refresh');
}

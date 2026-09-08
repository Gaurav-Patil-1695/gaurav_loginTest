import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import * as authApi from '../api/auth';
import type { User } from '../api/types';
import { getAccessToken, clearTokens, setAccessToken } from './tokenStore';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (
    fullName: string,
    email: string,
    password: string,
    confirmPassword: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refresh = useCallback(async () => {
    try {
      const response = await authApi.refresh();
      setAccessToken(response.accessToken);
      const meResponse = await authApi.me();
      setUser(meResponse);
    } catch {
      setUser(null);
      clearTokens();
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();
      if (token) {
        try {
          const meResponse = await authApi.me();
          setUser(meResponse);
        } catch {
          try {
            await refresh();
          } catch {
            setUser(null);
            clearTokens();
          }
        }
      } else {
        try {
          await refresh();
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string, rememberMe = false) => {
      const response = await authApi.login({ email, password, rememberMe });
      setAccessToken(response.accessToken);
      const meResponse = await authApi.me();
      setUser(meResponse);
    },
    [],
  );

  const register = useCallback(
    async (
      fullName: string,
      email: string,
      password: string,
      confirmPassword: string,
    ) => {
      const response = await authApi.register({
        fullName,
        email,
        password,
        confirmPassword,
      });
      setAccessToken(response.accessToken);
      const meResponse = await authApi.me();
      setUser(meResponse);
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      clearTokens();
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      refresh,
    }),
    [user, isLoading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

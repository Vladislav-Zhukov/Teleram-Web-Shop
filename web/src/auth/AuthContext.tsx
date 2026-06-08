import React, { createContext, useEffect, useMemo, useState } from "react";
import { tokenStorage, request } from "../api/http";
import * as AuthAPI from "../api/auth";

type User = { id: number; email: string; is_admin: boolean; telegram_id?: number | null };

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshMe() {
    try {
      const me = await request<User>("/users/me", { auth: true });
      setUser(me);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    (async () => {
      await refreshMe();
      setLoading(false);
    })();
  }, []);

  async function login(email: string, password: string) {
    await AuthAPI.login(email, password);
    await refreshMe();
  }

  async function register(email: string, password: string) {
    await AuthAPI.register(email, password);
    await login(email, password);
  }

  async function logout() {
    const { refresh } = tokenStorage.readTokens();
    if (refresh) {
      try { await AuthAPI.logout(refresh); } catch {}
    }
    tokenStorage.clearTokens();
    setUser(null);
  }

  const value = useMemo<AuthState>(() => ({ user, loading, login, register, logout, refreshMe }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

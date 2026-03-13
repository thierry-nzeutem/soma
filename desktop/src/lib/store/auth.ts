'use client';
// ─── SOMA Desktop — Zustand Auth Store ──────────────────────────────────────
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  username: string | null;
  isAuthenticated: boolean;
  _hasHydrated: boolean;

  setTokens: (accessToken: string, refreshToken: string) => void;
  setUsername: (username: string) => void;
  logout: () => void;
  setHasHydrated: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      username: null,
      isAuthenticated: false,
      _hasHydrated: false,

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken, isAuthenticated: true }),

      setUsername: (username) => set({ username }),

      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          username: null,
          isAuthenticated: false,
        }),

      setHasHydrated: (v) => set({ _hasHydrated: v }),
    }),
    {
      name: 'soma-auth',
      version: 1,
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        username: state.username,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

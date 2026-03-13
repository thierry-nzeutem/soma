'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useTranslations } from '@/lib/i18n/config';
import { Sidebar } from './sidebar';
import { TopBar } from './top-bar';
import { MobileNav } from './mobile-nav';

interface AppShellProps {
  children: React.ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function AppShell({ children, onRefresh, isRefreshing }: AppShellProps) {
  const router = useRouter();
  const t = useTranslations();
  const {
    isAuthenticated,
    accessToken,
    refreshToken,
    setTokens,
    _hasHydrated,
  } = useAuthStore();

  useEffect(() => {
    // Wait for Zustand to hydrate from localStorage before checking auth
    if (!_hasHydrated) return;

    async function tryRefresh() {
      if (refreshToken && !accessToken) {
        try {
          const { default: axios } = await import('axios');
          const { data } = await axios.post('/auth/refresh', { refresh_token: refreshToken });
          setTokens(data.access_token, data.refresh_token);
        } catch {
          router.push('/login');
        }
      } else if (!isAuthenticated && !refreshToken) {
        router.push('/login');
      }
    }
    tryRefresh();
  }, [_hasHydrated]); // eslint-disable-line react-hooks/exhaustive-deps

  // Block rendering until Zustand has hydrated from localStorage
  if (!_hasHydrated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-soma-bg">
        <div className="animate-pulse text-soma-muted text-sm">{t('common.loading')}</div>
      </div>
    );
  }

  if (!isAuthenticated && !refreshToken) {
    return null; // Will redirect
  }

  return (
    <div className="flex flex-col lg:flex-row h-screen w-screen overflow-hidden bg-soma-bg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar onRefresh={onRefresh} isRefreshing={isRefreshing} />
        <main className="flex-1 overflow-hidden pb-16 lg:pb-0">{children}</main>
      </div>
      <MobileNav />
    </div>
  );
}

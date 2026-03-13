'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { login } from '@/lib/api/auth';
import { cn } from '@/lib/utils';
import { Activity, Eye, EyeOff, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUsername } = useAuthStore();

  const [username, setUsernameInput] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const tokens = await login({ username: username.trim(), password });
      setTokens(tokens.access_token, tokens.refresh_token);
      setUsername(username.trim());
      router.push('/dashboard');
    } catch (err: unknown) {
      const axiosError = err as { response?: { status: number } };
      if (axiosError?.response?.status === 401) {
        setError('Identifiants incorrects. Vérifiez votre nom d\'utilisateur et mot de passe.');
      } else {
        setError('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-soma-bg flex items-center justify-center">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-soma-bg via-[#0D1A14] to-soma-bg pointer-events-none" />

      <div className="relative w-full max-w-md px-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-14 h-14 rounded-2xl bg-soma-accent flex items-center justify-center mb-4 glow-accent">
            <Activity className="w-7 h-7 text-black" strokeWidth={2.5} />
          </div>
          <h1 className="text-3xl font-bold text-soma-text tracking-tight">SOMA</h1>
          <p className="text-soma-text-secondary text-sm mt-1">Personal Health Intelligence</p>
        </div>

        {/* Login card */}
        <div className="card-surface p-8">
          <h2 className="text-xl font-semibold text-soma-text mb-6">Connexion</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-soma-text-secondary mb-1.5"
              >
                Nom d&apos;utilisateur
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsernameInput(e.target.value)}
                autoComplete="username"
                autoFocus
                disabled={loading}
                className={cn(
                  'w-full px-3.5 py-2.5 rounded-lg text-soma-text text-sm',
                  'bg-[#0D0D0D] border border-soma-border',
                  'placeholder:text-soma-text-muted',
                  'focus:outline-none focus:border-soma-accent focus:ring-1 focus:ring-soma-accent',
                  'disabled:opacity-50 transition-colors'
                )}
                placeholder="votre_username"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-soma-text-secondary mb-1.5"
              >
                Mot de passe
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  disabled={loading}
                  className={cn(
                    'w-full px-3.5 py-2.5 pr-10 rounded-lg text-soma-text text-sm',
                    'bg-[#0D0D0D] border border-soma-border',
                    'placeholder:text-soma-text-muted',
                    'focus:outline-none focus:border-soma-accent focus:ring-1 focus:ring-soma-accent',
                    'disabled:opacity-50 transition-colors'
                  )}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-soma-text-muted hover:text-soma-text-secondary transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="text-soma-danger text-sm bg-soma-danger/10 border border-soma-danger/20 rounded-lg px-3.5 py-2.5">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className={cn(
                'w-full py-2.5 rounded-lg text-sm font-semibold transition-all mt-2',
                'bg-soma-accent text-black',
                'hover:bg-soma-accent-dim',
                'disabled:opacity-40 disabled:cursor-not-allowed',
                'flex items-center justify-center gap-2'
              )}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connexion…
                </>
              ) : (
                'Se connecter'
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-soma-text-muted mt-6">
          SOMA Desktop v1.0 — Connecté à localhost:8000
        </p>
      </div>
    </div>
  );
}

'use client';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  // Note: real superuser check is enforced by the API (403 if not superuser)
  // The frontend layout just shows admin navigation
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 pb-4 border-b border-soma-border">
        <a href="/admin" className="text-sm text-soma-text-muted hover:text-soma-text transition-colors">
          Dashboard
        </a>
        <a href="/admin/users" className="text-sm text-soma-text-muted hover:text-soma-text transition-colors">
          Utilisateurs
        </a>
        <a href="/admin/settings" className="text-sm text-soma-text-muted hover:text-soma-text transition-colors">
          Paramètres
        </a>
      </div>
      {children}
    </div>
  );
}

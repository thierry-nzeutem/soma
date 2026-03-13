import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { ThemeInitializer } from '@/components/ui/theme-initializer';

export const metadata: Metadata = {
  title: 'SOMA — Personal Health Intelligence',
  description: 'Your personal health intelligence dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        {/* Prevent flash of wrong theme/locale — apply stored preferences before paint */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var stored = JSON.parse(localStorage.getItem('soma-theme') || '{}');
                  var mode = stored.state && stored.state.mode ? stored.state.mode : 'light';
                  if (mode === 'system') {
                    mode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  if (mode === 'dark') {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
                try {
                  var localeStored = JSON.parse(localStorage.getItem('soma-locale') || '{}');
                  var locale = localeStored.state && localeStored.state.locale ? localeStored.state.locale : 'fr';
                  document.documentElement.lang = locale;
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="bg-soma-bg text-soma-text antialiased overflow-hidden">
        <Providers>
          <ThemeInitializer />
          {children}
        </Providers>
      </body>
    </html>
  );
}

import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // SOMA design system — uses CSS variables for theme switching
        soma: {
          bg: 'var(--soma-bg)',
          surface: 'var(--soma-surface)',
          'surface-variant': 'var(--soma-surface-variant)',
          border: 'var(--soma-border)',
          accent: 'var(--soma-accent)',
          'accent-dim': '#00B47A',
          text: 'var(--soma-text)',
          'text-secondary': 'var(--soma-text-secondary)',
          'text-muted': 'var(--soma-muted)',
          muted: 'var(--soma-muted)',
          warning: 'var(--soma-warning)',
          danger: 'var(--soma-danger)',
          success: 'var(--soma-success)',
          info: '#00B4D8',
          'nav-bg': 'var(--soma-nav-bg)',
          'card-bg': 'var(--soma-card-bg)',
        },
      },
      backgroundColor: {
        DEFAULT: 'var(--soma-bg)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-in': 'slideIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};

export default config;

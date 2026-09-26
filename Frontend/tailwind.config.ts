import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: 'var(--color-bg-primary)',
          secondary: 'var(--color-bg-secondary)',
          tertiary: 'var(--color-bg-tertiary)',
          elevated: 'var(--color-bg-elevated)',
        },
        surface: {
          card: 'var(--color-surface-card)',
          hover: 'var(--color-surface-hover)',
          active: 'var(--color-surface-active)',
        },
        border: {
          default: 'var(--color-border-default)',
          hover: 'var(--color-border-hover)',
          active: 'var(--color-border-active)',
        },
        accent: {
          primary: 'var(--color-accent-primary)',
          'primary-hover': 'var(--color-accent-primary-hover)',
          'primary-muted': 'var(--color-accent-primary-muted)',
          cyan: 'var(--color-accent-cyan)',
          'cyan-hover': 'var(--color-accent-cyan-hover)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          subtle: 'var(--color-text-subtle)',
          'on-accent': 'var(--color-text-on-accent)',
        },
        error: '#EF4444',
        success: '#10B981',
        warning: '#F59E0B',
        info: '#3B82F6',
        jewel: {
          sapphire: '#1e40af',
          'sapphire-light': '#3b82f6',
          emerald: '#047857',
          'emerald-light': '#10b981',
          ruby: '#991b1b',
          'ruby-light': '#ef4444',
          copper: '#92400e',
          'copper-light': '#d97706',
        },
        metal: {
          gold: '#d4a853',
          'gold-light': '#f0d78c',
          silver: '#94a3b8',
          brass: '#b8860b',
        },
      },
      fontFamily: {
        heading: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'card': 'var(--radius-lg)',
        'card-lg': 'var(--radius-xl)',
        'pill': '100px',
        'input': 'var(--radius-md)',
        'button': 'var(--radius-md)',
        'btn': 'var(--radius-md)',
        'modal': 'var(--radius-xl)',
      },
    },
  },
  plugins: [],
};

export default config;

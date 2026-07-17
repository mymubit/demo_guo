/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        shell: {
          DEFAULT: 'var(--shell-bg)',
          elevated: 'var(--shell-bg-elevated)',
          ink: 'var(--shell-ink)',
          muted: 'var(--shell-ink-muted)',
          accent: 'var(--accent-shell)',
          'accent-hover': 'var(--accent-shell-hover)',
        },
        action: {
          DEFAULT: 'var(--accent-action)',
          hover: 'var(--accent-action-hover)',
        },
        canvas: {
          DEFAULT: 'var(--canvas)',
          muted: 'var(--canvas-muted)',
        },
        surface: 'var(--surface)',
        border: 'var(--border)',
        ink: {
          DEFAULT: 'var(--ink)',
          muted: 'var(--ink-muted)',
          faint: 'var(--ink-faint)',
        },
        danger: 'var(--danger)',
        success: 'var(--success)',
        warning: 'var(--warning)',
        // 过渡期：旧 navy 类名仍可用，映射到 shell
        navy: {
          950: '#030d24',
          900: 'var(--shell-bg)',
          800: 'var(--shell-bg-elevated)',
          700: '#1a2d4d',
          600: '#243a5c',
        },
        gold: {
          300: 'var(--accent-shell-hover)',
          400: 'var(--accent-shell)',
          500: '#d9a014',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Noto Sans SC"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"IBM Plex Sans"', '"Noto Sans SC"', 'ui-sans-serif', 'sans-serif'],
      },
      minWidth: {
        pc: '1280px',
      },
      boxShadow: {
        panel: '0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 12px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
}

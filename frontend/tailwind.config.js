/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#030d24',
          900: '#0a1628',
          800: '#12203a',
          700: '#1a2d4d',
          600: '#243a5c',
        },
        canvas: {
          DEFAULT: '#f4f5f7',
          muted: '#e8eaee',
          raised: '#ffffff',
        },
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
        gold: {
          300: '#f7cb54',
          400: '#f4b719',
          500: '#d9a014',
        },
        ink: {
          DEFAULT: '#0f172a',
          muted: '#475569',
          faint: '#94a3b8',
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

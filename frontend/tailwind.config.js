/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 深色主题色
        navy: {
          50: '#f0f4fa',
          100: '#d9e2f0',
          200: '#b3c5e1',
          300: '#8da7d3',
          400: '#4d6db5',
          500: '#2d4f9e',
          600: '#1a3a7a',
          700: '#0f2a5c',
          800: '#0a1f44',
          900: '#051437',
          950: '#030d24',
        },
        // 金色强调色
        gold: {
          50: '#fef9ec',
          100: '#fdf0c9',
          200: '#fae08f',
          300: '#f7cb54',
          400: '#f4b719',
          500: '#e0a008',
          600: '#b37c06',
          700: '#805904',
          800: '#4d3603',
          900: '#261b01',
        },
        // 业务系统中性色
        neutral: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        // 语义状态色
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        info: {
          50: '#ecfeff',
          100: '#cffafe',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
        },
        // 渐变色
        gradient: {
          primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          gold: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
          navy: 'linear-gradient(135deg, #0a1f44 0%, #0f2a5c 100%)',
          dark: 'linear-gradient(180deg, #030d24 0%, #051437 100%)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['12px', '18px'],
        'sm': ['14px', '22px'],
        'base': ['16px', '26px'],
        'lg': ['18px', '30px'],
        'xl': ['20px', '32px'],
        '2xl': ['24px', '38px'],
        '3xl': ['32px', '48px'],
        '4xl': ['40px', '56px'],
        '5xl': ['48px', '64px'],
        '6xl': ['60px', '72px'],
      },
      boxShadow: {
        premium: '0 18px 60px -24px rgba(102, 126, 234, 0.55)',
        gold: '0 16px 42px -20px rgba(244, 183, 25, 0.55)',
        card: '0 12px 36px -24px rgba(0, 0, 0, 0.45)',
        'card-hover': '0 20px 52px -28px rgba(0, 0, 0, 0.65)',
        soft: '0 8px 28px -22px rgba(15, 42, 92, 0.65)',
        modal: '0 24px 80px -32px rgba(0, 0, 0, 0.72)',
      },
      borderRadius: {
        card: '1rem',
        panel: '1.25rem',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'fadeInUp': 'fadeInUp 0.6s ease-out',
        'fadeIn': 'fadeIn 0.6s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

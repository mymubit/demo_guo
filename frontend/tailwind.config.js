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
        'premium': '0 10px 40px -10px rgba(102, 126, 234, 0.3)',
        'gold': '0 10px 40px -10px rgba(244, 183, 25, 0.3)',
        'card': '0 4px 24px -4px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 12px 40px -8px rgba(0, 0, 0, 0.15)',
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

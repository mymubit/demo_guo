/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      // ============ SF-Token: 色彩体系 ============
      // 语义化命名，避免与 Tailwind 默认色板冲突
      colors: {
        // 主品牌色: 深蓝-紫色渐变 — 用于主 CTA、重要强调
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        // 强调色: 金色 — 用于高分、亮点、二次强调
        accent: {
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
        // ⬇ gold-* 作为 accent-* 的别名 — 老代码与 golden highlight 场景使用
        // 长期目标: 统一迁移到 accent-*
        gold: {
          100: '#fdf0c9',
          200: '#fae08f',
          300: '#f7cb54',
          400: '#f4b719',
          500: '#e0a008',
          600: '#b37c06',
        },
        // 深色底: 保持 nav 系列，作为内容场景底色
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
        // 中性色: 管理后台、卡片、表格主用
        slate: {
          25: '#f8fafc',
          50: '#f1f5f9',
          100: '#e2e8f0',
          200: '#cbd5e1',
          300: '#94a3b8',
          400: '#64748b',
          500: '#475569',
          600: '#334155',
          700: '#1e293b',
          800: '#0f172a',
          850: '#0b1120',
          900: '#020617',
          950: '#030d24',
        },
        // 语义状态色 — 统一带 bg/light/dark，组件层直接使用
        success: {
          DEFAULT: '#22c55e',
          light: '#86efac',
          dark: '#15803d',
          bg: 'rgba(34, 197, 94, 0.12)',
          border: 'rgba(34, 197, 94, 0.30)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fcd34d',
          dark: '#b45309',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.30)',
        },
        danger: {
          DEFAULT: '#ef4444',
          light: '#fca5a5',
          dark: '#b91c1c',
          bg: 'rgba(239, 68, 68, 0.12)',
          border: 'rgba(239, 68, 68, 0.30)',
        },
        info: {
          DEFAULT: '#06b6d4',
          light: '#67e8f9',
          dark: '#0e7490',
          bg: 'rgba(6, 182, 212, 0.12)',
          border: 'rgba(6, 182, 212, 0.30)',
        },
        // 渐变色: 可用于 bg-gradient 类
        gradient: {
          brand: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          accent: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
          dark: 'linear-gradient(180deg, #030d24 0%, #051437 100%)',
        },
      },

      // ============ SF-Token: 字体体系 ============
      // Tailwind 语义: ['fontSize', 'lineHeight']
      // 为避免字号混乱，统一命名与设计稿对应
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontWeight: {
        regular: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      fontSize: {
        '2xs': ['11px', { lineHeight: '16px', letterSpacing: '0.01em' }],
        xs: ['12px', { lineHeight: '18px', letterSpacing: '0.01em' }],
        sm: ['13px', { lineHeight: '20px', letterSpacing: '0' }],
        base: ['14px', { lineHeight: '22px', letterSpacing: '0' }],
        md: ['15px', { lineHeight: '24px', letterSpacing: '0' }],
        lg: ['16px', { lineHeight: '26px', letterSpacing: '0' }],
        xl: ['18px', { lineHeight: '28px', letterSpacing: '-0.01em' }],
        '2xl': ['20px', { lineHeight: '30px', letterSpacing: '-0.02em' }],
        '3xl': ['24px', { lineHeight: '32px', letterSpacing: '-0.02em' }],
        '4xl': ['30px', { lineHeight: '38px', letterSpacing: '-0.03em' }],
        '5xl': ['36px', { lineHeight: '44px', letterSpacing: '-0.03em' }],
        '6xl': ['48px', { lineHeight: '56px', letterSpacing: '-0.04em' }],
      },

      // ============ SF-Token: 间距体系 ============
      spacing: {
        0: '0',
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        20: '80px',
        24: '96px',
      },

      // ============ SF-Token: 圆角体系 ============
      borderRadius: {
        none: '0',
        sm: '6px',
        DEFAULT: '8px',
        md: '10px',
        lg: '14px',
        xl: '18px',
        '2xl': '24px',
        full: '9999px',
        // 场景专用
        card: '18px',
        panel: '20px',
        input: '10px',
        badge: '9999px',
      },

      // ============ SF-Token: 阴影层级 ============
      boxShadow: {
        none: 'none',
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 2px 8px -4px rgba(0, 0, 0, 0.4)',
        DEFAULT: '0 4px 16px -8px rgba(0, 0, 0, 0.5)',
        md: '0 8px 32px -12px rgba(0, 0, 0, 0.55)',
        lg: '0 16px 56px -20px rgba(0, 0, 0, 0.65)',
        xl: '0 24px 80px -32px rgba(0, 0, 0, 0.72)',
        // 场景专用
        panel: '0 12px 36px -24px rgba(0, 0, 0, 0.45)',
        card: '0 12px 36px -24px rgba(0, 0, 0, 0.45)',
        'card-hover': '0 20px 52px -28px rgba(0, 0, 0, 0.65)',
        modal: '0 24px 80px -32px rgba(0, 0, 0, 0.72)',
        premium: '0 18px 60px -24px rgba(102, 126, 234, 0.55)',
        'brand-glow': '0 0 24px rgba(102, 126, 234, 0.35)',
        glow: '0 0 20px rgba(244, 183, 25, 0.25)',
        gold: '0 16px 42px -20px rgba(244, 183, 25, 0.55)',
      },

      // ============ SF-Token: 边框 ============
      borderColor: {
        DEFAULT: 'rgba(255, 255, 255, 0.08)',
        subtle: 'rgba(255, 255, 255, 0.04)',
        strong: 'rgba(255, 255, 255, 0.16)',
        accent: 'rgba(244, 183, 25, 0.30)',
        brand: 'rgba(102, 126, 234, 0.30)',
      },

      // ============ SF-Token: 动画与动效 ============
      transitionDuration: {
        0: '0ms',
        75: '75ms',
        100: '100ms',
        150: '150ms',
        200: '200ms',
        300: '300ms',
        400: '400ms',
        500: '500ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
        'ease-in': 'cubic-bezier(0.4, 0, 1, 1)',
        'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      animation: {
        'fade-in': 'fadeIn 0.25s ease-out',
        'fade-in-up': 'fadeInUp 0.3s ease-out',
        'fade-in-scale': 'fadeInScale 0.25s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'spin-fast': 'spin 0.8s linear infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        shimmer: 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInScale: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(244, 183, 25, 0.2)' },
          '50%': { boxShadow: '0 0 20px rgba(244, 183, 25, 0.5)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
}

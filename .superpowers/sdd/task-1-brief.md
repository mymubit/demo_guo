### Task 1: Design Token + Tailwind 映射

**Files:**
- Modify: `frontend/src/styles/index.css`
- Modify: `frontend/tailwind.config.js`
- Test: `frontend/src/styles/tokens.test.ts`（新建，断言关键 CSS 变量字符串存在于源文件）

**Interfaces:**
- Consumes: 规格 §4 token 表
- Produces: CSS 变量 `--shell-bg`、`--accent-shell`、`--accent-action`、`--canvas`、`--surface` 等；Tailwind 色名 `shell`、`action`、`canvas`、`surface`、`ink`

- [ ] **Step 1: Write the failing test**

创建 `frontend/src/styles/tokens.test.ts`:

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const css = readFileSync(resolve(__dirname, 'index.css'), 'utf8')
const tw = readFileSync(resolve(__dirname, '../../tailwind.config.js'), 'utf8')

describe('design tokens', () => {
  it('defines dual accents and cold mist canvas', () => {
    expect(css).toContain('--accent-shell: #f4b719')
    expect(css).toContain('--accent-action: #0f2744')
    expect(css).toContain('--canvas: #eef1f5')
    expect(css).toContain('--shell-bg: #0a1628')
  })

  it('does not keep indigo brand-500 as system brand', () => {
    expect(css).not.toContain('--brand-500: #6366f1')
    expect(tw).not.toMatch(/brand:\s*\{[^}]*500:\s*'#6366f1'/)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/styles/tokens.test.ts -v`

Expected: FAIL（变量尚未写入或仍含 indigo）

- [ ] **Step 3: Write minimal implementation**

替换 `frontend/src/styles/index.css` 的 `:root` 与 `body` 为：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --shell-bg: #0a1628;
  --shell-bg-elevated: #12203a;
  --shell-ink: #e8eef7;
  --shell-ink-muted: #94a3b8;
  --accent-shell: #f4b719;
  --accent-shell-hover: #f7cb54;

  --canvas: #eef1f5;
  --canvas-muted: #e4e9f0;
  --surface: #ffffff;
  --border: #d8dee8;

  --accent-action: #0f2744;
  --accent-action-hover: #163a66;
  --focus-ring: rgba(15, 39, 68, 0.28);

  --ink: #0f172a;
  --ink-muted: #475569;
  --ink-faint: #94a3b8;

  --danger: #dc2626;
  --success: #159947;
  --warning: #d97706;
}

html,
body,
#root {
  height: 100%;
}

body {
  margin: 0;
  min-width: 1280px;
  background: var(--canvas);
  color: var(--ink);
  font-family: 'IBM Plex Sans', 'Noto Sans SC', ui-sans-serif, system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

@layer components {
  .sf-control {
    @apply w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink
      placeholder:text-ink-faint outline-none transition
      focus:border-action focus:ring-2 focus:ring-action/20;
  }

  .sf-label {
    @apply mb-1.5 block text-sm font-medium text-ink;
  }

  .sf-section-title {
    @apply text-lg font-semibold tracking-tight text-ink;
  }

  .sf-panel {
    @apply rounded-xl border border-border bg-surface shadow-panel;
  }
}
```

替换 `frontend/tailwind.config.js` 的 `theme.extend.colors`（保留 `navy` 若仍被引用，但主路径改用 shell/action）：

```js
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/styles/tokens.test.ts -v`

Expected: PASS

Run: `cd frontend && npm run typecheck`

Expected: 可能因下游仍引用 `brand-*` 而失败——若失败，先只保证 tokens 测试 PASS；在 Task 2–3 清引用。若 typecheck 仅 CSS/无 TS 错误则 PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles/index.css frontend/tailwind.config.js frontend/src/styles/tokens.test.ts
git commit -m "$(cat <<'EOF'
feat(ui): introduce dual-accent design tokens

EOF
)"
```

---


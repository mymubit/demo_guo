# Frontend Visual Quasi-Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准规格，将 ScriptForge 前端准重写为「影棚壳层 + 冷雾内容 + 双强调色」，先 Design System 再同一里程碑换完全部页面。

**Architecture:** CSS 变量为色板 SSOT，Tailwind 映射变量；通用 primitive 走 shadcn/Radix 主题化；`AppShell`/`PageShell` 与 `components/workbench/*` 自研但共用 token。业务 `services`/`hooks`/`types` 复用，后端契约不动。

**Tech Stack:** React 18、Vite 5、TypeScript strict、Tailwind 3、React Query、React Router 6、lucide-react、shadcn/ui（Radix + `class-variance-authority` + `cn`）、Vitest。

## Global Constraints

- 规格 SSOT：`docs/superpowers/specs/2026-07-17-frontend-visual-rewrite-design.md`（已批准）。
- 侧栏 active / 壳层高亮只用 `--accent-shell`（橙金）；页内主 CTA / focus / 链接只用 `--accent-action`（墨海军蓝）。
- 禁止 indigo/`brand-500: #6366f1` 作为主色；禁止新增大功能与后端契约变更。
- 禁止引入 Ant Design / MUI；新增依赖仅限 shadcn 所需（`class-variance-authority`、`@radix-ui/*`、`tailwindcss-animate` 等）。
- 保留 `min-width: 1280px`（`PC_MIN_WIDTH` / `min-w-pc`）。
- 代码注释默认中文；commit message 用英文 conventional 前缀（`feat:` / `fix:` / `test:` / `refactor:` / `chore:`）。
- 每个 Task 结束后跑：`cd frontend && npm run typecheck`；涉及 UI 行为时再跑相关 vitest。
- Figma/MCP 非本计划门禁。

---

## File Structure

| 文件 | 职责 |
|------|------|
| `frontend/src/styles/index.css` | CSS 变量 + `@layer` 基础样式；移除旧 indigo brand 变量 |
| `frontend/tailwind.config.js` | 颜色映射到 CSS 变量；删除 `brand.*` indigo 色阶 |
| `frontend/components.json` | shadcn 配置（若 CLI 初始化生成） |
| `frontend/src/components/ui/Button.tsx` | `action`/`secondary`/`ghost`/`danger`/`shell` 变体 |
| `frontend/src/components/ui/Badge.tsx` | `action` 替代 `brand` tone |
| `frontend/src/components/ui/Tabs.tsx` | active 态改海军蓝 |
| `frontend/src/components/ui/*` | 按需增加 Input/Dialog/Table 等 shadcn 组件 |
| `frontend/src/components/ui/button.test.tsx` | Button 变体单测（新建） |
| `frontend/src/components/layout/AppShell.tsx` | 影棚侧栏；橙金 active |
| `frontend/src/components/layout/PageShell.tsx` | 冷雾页头 + 版心 |
| `frontend/src/pages/*.tsx` | 全部页面按新 token/布局换装 |
| `frontend/src/components/workbench/*` | 顶区紧凑 + 面板冷雾；去掉 brand 类名 |
| `frontend/src/components/theme/ThemeMatrixPicker.tsx` | brand → action |
| `frontend/src/components/artifacts/*` | brand → action |

```text
Token (index.css)
    │
    ▼
Tailwind theme.extend.colors
    │
    ├── components/ui (shadcn + Button)
    ├── layout/AppShell (accent-shell)
    ├── layout/PageShell (cold mist)
    └── pages + workbench (accent-action)
```

---

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

### Task 2: Button 变体重命名（action / shell）

**Files:**
- Modify: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/button.test.tsx`
- Modify: 所有 `variant="brand"` → `variant="action"`；页内 `variant="gold"` → 评估改为 `action`（壳层点缀保留 `shell`）

**Interfaces:**
- Consumes: Tailwind `action` / `shell.accent`
- Produces: `Button` props `variant?: 'action' | 'secondary' | 'ghost' | 'danger' | 'shell'`；默认 `action`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('defaults to action variant classes', () => {
    render(<Button>保存</Button>)
    const el = screen.getByRole('button', { name: '保存' })
    expect(el.className).toMatch(/bg-action/)
    expect(el.className).not.toMatch(/bg-brand/)
  })

  it('supports shell variant for chrome-only accents', () => {
    render(<Button variant="shell">壳层</Button>)
    expect(screen.getByRole('button', { name: '壳层' }).className).toMatch(/bg-shell-accent|bg-gold/)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/ui/button.test.tsx -v`

Expected: FAIL（仍为 `brand`）

- [ ] **Step 3: Write minimal implementation**

`Button.tsx`：

```tsx
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/cn'

type Variant = 'action' | 'secondary' | 'ghost' | 'danger' | 'shell'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  size?: Size
  iconLeft?: ReactNode
  loading?: boolean
}

const variantClass: Record<Variant, string> = {
  action: 'bg-action text-white hover:bg-action-hover border-transparent',
  secondary: 'bg-surface text-ink border-border hover:bg-canvas-muted',
  ghost: 'bg-transparent text-ink-muted border-transparent hover:bg-canvas-muted',
  danger: 'bg-danger text-white hover:opacity-90 border-transparent',
  shell: 'bg-shell-accent text-shell hover:bg-shell-accent-hover border-transparent font-medium',
}

const sizeClass: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
}

export function Button({
  variant = 'action',
  size = 'md',
  iconLeft,
  loading,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg border font-medium transition disabled:cursor-not-allowed disabled:opacity-50',
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent" />
      ) : (
        iconLeft
      )}
      {children}
    </button>
  )
}
```

全仓替换：

- `variant="brand"` → `variant="action"`（或删属性，因默认已是 action）
- 页内主操作上的 `variant="gold"` → `variant="action"`
- 仅壳层品牌点缀保留 `variant="shell"`

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/components/ui/button.test.tsx -v && npm run typecheck`

Expected: PASS（若他处仍传 `brand`，typecheck FAIL——一并改完）

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Button.tsx frontend/src/components/ui/button.test.tsx
git add -u frontend/src
git commit -m "$(cat <<'EOF'
feat(ui): replace brand button with action and shell variants

EOF
)"
```

---

### Task 3: Badge + Tabs 去 indigo

**Files:**
- Modify: `frontend/src/components/ui/Badge.tsx`
- Modify: `frontend/src/components/ui/Tabs.tsx`
- Create: `frontend/src/components/ui/badge-tabs.test.tsx`
- Modify: 引用 `tone="brand"` 的调用方 → `tone="action"`

**Interfaces:**
- Consumes: `action` / `border` token
- Produces: `Badge` tone `'action' | 'gold' | 'success' | 'warning' | 'danger' | 'info' | 'default'`；Tabs active 使用 `text-action` + `bg-action`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from './Badge'
import { Tabs } from './Tabs'

describe('Badge and Tabs accents', () => {
  it('action tone avoids brand classes', () => {
    render(<Badge tone="action">进行中</Badge>)
    expect(screen.getByText('进行中').className).not.toMatch(/brand/)
    expect(screen.getByText('进行中').className).toMatch(/action/)
  })

  it('tabs active uses action underline', () => {
    render(
      <Tabs
        items={[{ id: 'a', label: '全部' }]}
        value="a"
        onChange={() => undefined}
      />,
    )
    const tab = screen.getByRole('tab', { name: '全部' })
    expect(tab.className).toMatch(/text-action/)
  })
})
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `cd frontend && npx vitest run src/components/ui/badge-tabs.test.tsx -v`

- [ ] **Step 3: Implement**

`Badge.tsx` 中 `brand` → `action`：

```ts
action: 'bg-action/10 text-action border-action/20',
```

删除 `brand` tone。全仓 `tone="brand"` → `tone="action"`。

`Tabs.tsx` active：

```tsx
active ? 'text-action' : 'text-ink-muted hover:text-ink',
// underline:
<span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-action" />
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/components/ui/badge-tabs.test.tsx -v && npm run typecheck`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Badge.tsx frontend/src/components/ui/Tabs.tsx frontend/src/components/ui/badge-tabs.test.tsx
git add -u frontend/src
git commit -m "$(cat <<'EOF'
refactor(ui): point Badge and Tabs accents to action token

EOF
)"
```

---

### Task 4: 安装 shadcn 依赖并落地最小 primitive 集

**Files:**
- Modify: `frontend/package.json` / lockfile
- Create: `frontend/components.json`（若 CLI 生成）
- Create/Modify: `frontend/src/components/ui/input.tsx`、`dialog.tsx`、`table.tsx`、`dropdown-menu.tsx`（名称以 CLI 为准；若与现有 `Button.tsx` 冲突，保留现有 Button，勿覆盖 Task 2 变体）
- Modify: `frontend/tailwind.config.js` — 按需加 `tailwindcss-animate`

**Interfaces:**
- Consumes: Task 1 tokens（把 shadcn CSS 变量映射到 `--accent-action` 等）
- Produces: 可 import 的 Input/Dialog/Table/DropdownMenu；**不替换**业务页逻辑，仅备后续页换装使用

- [ ] **Step 1: Write the failing smoke test**

Create `frontend/src/components/ui/shadcn-smoke.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'

describe('shadcn primitives', () => {
  it('exposes Input module', async () => {
    const mod = await import('./input')
    expect(mod.Input).toBeTypeOf('function')
  })
})
```

- [ ] **Step 2: Run — expect FAIL（模块不存在）**

Run: `cd frontend && npx vitest run src/components/ui/shadcn-smoke.test.tsx -v`

- [ ] **Step 3: Install + generate**

在 `frontend/`：

```bash
npm install class-variance-authority @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-slot tailwindcss-animate
npx shadcn@latest init -y
npx shadcn@latest add input dialog table dropdown-menu -y
```

若 `shadcn add button` 会覆盖自定义 Button：**跳过 button**，保留 Task 2 文件。

在 `index.css` 的 `:root` 增加 shadcn 兼容映射（示例）：

```css
--background: var(--canvas);
--foreground: var(--ink);
--primary: var(--accent-action);
--primary-foreground: #ffffff;
--ring: var(--accent-action);
--border: var(--border);
--card: var(--surface);
```

`tailwind.config.js` 的 `plugins` 加入 `require('tailwindcss-animate')` 或 ESM `import tailwindcssAnimate from 'tailwindcss-animate'`。

- [ ] **Step 4: Run smoke + typecheck**

Run: `cd frontend && npx vitest run src/components/ui/shadcn-smoke.test.tsx -v && npm run typecheck`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/components.json frontend/src/components/ui frontend/src/styles/index.css frontend/tailwind.config.js
git commit -m "$(cat <<'EOF'
feat(ui): add shadcn primitives themed to action tokens

EOF
)"
```

---

### Task 5: AppShell 影棚侧栏（橙金 active）

**Files:**
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/AppShell.test.tsx`

**Interfaces:**
- Consumes: `shell` / `gold`/`shell-accent` tokens；现有 `NAV_GROUPS`
- Produces: 侧栏 `bg-shell`；active 项含 `ring-shell-accent` 或 `bg-shell-accent/15`；主区 `bg-canvas`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    auth: { user: { username: 'demo', nickname: '演示' } },
    logout: vi.fn(),
  }),
}))

vi.mock('@/hooks/useRecentProjects', () => ({
  useRecentProjects: () => [],
}))

import { AppShell } from './AppShell'

describe('AppShell', () => {
  it('marks projects nav with shell accent when active', () => {
    const qc = new QueryClient()
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/projects" element={<div>列表</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const link = screen.getByRole('link', { name: /项目/ })
    expect(link.className).toMatch(/gold|shell-accent|accent-shell/)
  })
})
```

- [ ] **Step 2: Run — expect FAIL 或弱断言失败则收紧实现后重跑**

Run: `cd frontend && npx vitest run src/components/layout/AppShell.test.tsx -v`

- [ ] **Step 3: Implement shell chrome**

关键 class 约定（在现有结构上替换）：

```tsx
// 根
className="flex h-dvh min-h-[720px] min-w-pc bg-canvas"

// aside
className="flex w-[clamp(11rem,15vw,15rem)] shrink-0 flex-col border-r border-shell-elevated bg-shell text-shell-ink"

// NavLink active
active
  ? 'bg-shell-accent/15 text-white ring-1 ring-shell-accent/40'
  : 'text-shell-muted hover:bg-white/5 hover:text-white'

// Logo 图标
<Clapperboard className="h-5 w-5 text-shell-accent" />
```

页内主 CTA 不要出现在侧栏；退出按钮继续 `ghost`。

- [ ] **Step 4: Run test + typecheck**

Run: `cd frontend && npx vitest run src/components/layout/AppShell.test.tsx -v && npm run typecheck`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/AppShell.tsx frontend/src/components/layout/AppShell.test.tsx
git commit -m "$(cat <<'EOF'
feat(layout): restyle AppShell as studio chrome with shell accent

EOF
)"
```

---

### Task 6: PageShell 冷雾页头

**Files:**
- Modify: `frontend/src/components/layout/PageShell.tsx`
- Create: `frontend/src/components/layout/PageShell.test.tsx`

**Interfaces:**
- Consumes: 现有 `PageShellProps`
- Produces: 页头 `border-border`；标题 `text-ink`；容器仍支持 `fluid|form|narrow`

- [ ] **Step 1: Write failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PageShell } from './PageShell'

describe('PageShell', () => {
  it('renders cold-mist header border token', () => {
    const { container } = render(
      <PageShell title="项目列表" description="管理项目">
        <div>内容</div>
      </PageShell>,
    )
    expect(screen.getByRole('heading', { name: '项目列表' })).toBeInTheDocument()
    const header = container.querySelector('header')
    expect(header?.className).toMatch(/border-border|border-slate/)
  })
})
```

- [ ] **Step 2: Run — may PASS already；若 border 仍为 `slate-200/80`，改为 `border-border` 后断言含 `border-border`**

- [ ] **Step 3: Implement**

```tsx
<header className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-border pb-5">
  <div className={cn('min-w-0', width === 'fluid' ? 'max-w-4xl' : 'max-w-3xl')}>
    <h1 className="text-xl font-semibold tracking-tight text-ink">{title}</h1>
    {description ? (
      <div className="mt-1.5 text-sm leading-relaxed text-ink-muted">{description}</div>
    ) : null}
  </div>
  {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
</header>
```

外层保持 `px-6 py-7` 疏朗（冷雾）。

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/components/layout/PageShell.test.tsx -v`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/PageShell.tsx frontend/src/components/layout/PageShell.test.tsx
git commit -m "$(cat <<'EOF'
refactor(layout): align PageShell with cold-mist borders

EOF
)"
```

---

### Task 7: LoginPage 冷雾换装

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`

**Interfaces:**
- Consumes: `Button variant="action"`；token 背景
- Produces: 无 indigo；主按钮海军蓝；轻纹理可用 navy/橙低透明

- [ ] **Step 1: Write failing visual-contract test**

Create `frontend/src/pages/LoginPage.tokens.test.tsx`:

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const src = readFileSync(resolve(__dirname, 'LoginPage.tsx'), 'utf8')

describe('LoginPage tokens', () => {
  it('does not reference indigo brand utilities', () => {
    expect(src).not.toMatch(/brand-500|brand-600|#6366f1/)
  })
})
```

- [ ] **Step 2: Run — FAIL if still has brand**

- [ ] **Step 3: Restyle**

- 背景径向渐变中的颜色改为 `rgba(10,22,40,…)` / `rgba(244,183,25,…)`（已有可保留），删除任何 indigo。
- 主提交按钮：`<Button type="submit" variant="action" loading={loading}>`。
- 卡片容器：`sf-panel` 或 `rounded-xl border border-border bg-surface`。
- 输入：`sf-control`。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/LoginPage.tokens.test.tsx -v && npm run typecheck`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx frontend/src/pages/LoginPage.tokens.test.tsx
git commit -m "$(cat <<'EOF'
feat(pages): restyle login to cold-mist action accents

EOF
)"
```

---

### Task 8: 创作域页面（列表 / 新建 / 设置）

**Files:**
- Modify: `frontend/src/pages/ProjectListPage.tsx`
- Modify: `frontend/src/pages/NewProjectPage.tsx`
- Modify: `frontend/src/pages/ProjectSettingsPage.tsx`
- Create: `frontend/src/pages/create-domain.tokens.test.ts`

**Interfaces:**
- Consumes: `PageShell`、`Button action`、`Badge action`、冷雾面板
- Produces: 三页无 `brand-*`；列表主 CTA「新建项目」为 `action`

- [ ] **Step 1: Write failing scan test**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const files = ['ProjectListPage.tsx', 'NewProjectPage.tsx', 'ProjectSettingsPage.tsx']

describe('create-domain pages tokens', () => {
  for (const file of files) {
    it(`${file} has no indigo brand classes`, () => {
      const src = readFileSync(resolve(__dirname, file), 'utf8')
      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone=\"brand\"|variant=\"brand\"/)
    })
  }
})
```

- [ ] **Step 2: Run — expect FAIL on pages still using brand**

- [ ] **Step 3: Restyle each page**

统一规则（三页都执行）：

1. 所有 `bg-brand-*` / `text-brand-*` / `ring-brand-*` → `action` 等价类。
2. 主按钮默认 `action`；危险操作用 `danger`。
3. 列表：项目行用 `sf-panel` 或 `border-border bg-surface`；增加疏朗 `gap`；状态 Badge 用 `action`/`success`/`default`。
4. 新建/设置：表单控件统一 `sf-control` / shadcn `Input`；分区标题 `sf-section-title`。
5. **不改** `dramaApi` 调用与字段。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/create-domain.tokens.test.ts -v && npm run typecheck && npm run test`

Expected: 全绿或仅与本域无关的既有失败需先记录——本任务不得引入新失败。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ProjectListPage.tsx frontend/src/pages/NewProjectPage.tsx frontend/src/pages/ProjectSettingsPage.tsx frontend/src/pages/create-domain.tokens.test.ts
git commit -m "$(cat <<'EOF'
feat(pages): cold-mist restyle for project create domain

EOF
)"
```

---

### Task 9: 工作台混合密度换装

**Files:**
- Modify: `frontend/src/pages/WorkbenchPage.tsx`
- Modify: `frontend/src/components/workbench/PipelineRail.tsx`
- Modify: `frontend/src/components/workbench/StageCanvas.tsx`
- Modify: `frontend/src/components/workbench/ModulePanel.tsx`
- Modify: `frontend/src/components/workbench/GenerationJobPanel.tsx`
- Modify: `frontend/src/components/workbench/QualityLoopPanel.tsx`
- Modify: `frontend/src/components/workbench/GenerationTroubleCard.tsx`
- Modify: `frontend/src/components/workbench/JobLlmCallLogsPanel.tsx`
- Modify: `frontend/src/components/theme/ThemeMatrixPicker.tsx`
- Modify: `frontend/src/components/artifacts/ArtifactViews.tsx`
- Modify: `frontend/src/components/artifacts/StoryBibleView.tsx`
- Create: `frontend/src/pages/workbench.tokens.test.ts`

**Interfaces:**
- Consumes: 现有 workbench 数据流与测试 fixtures
- Produces: 顶栏/PipelineRail 紧凑 + shell/gold 点缀允许；面板区冷雾 + action CTA；无 indigo

- [ ] **Step 1: Write failing scan + keep existing tests**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const roots = [
  resolve(__dirname, 'WorkbenchPage.tsx'),
  resolve(__dirname, '../components/workbench'),
  resolve(__dirname, '../components/theme/ThemeMatrixPicker.tsx'),
]

describe('workbench tokens', () => {
  it('PipelineRail source has no indigo brand utilities', () => {
    const src = readFileSync(resolve(__dirname, '../components/workbench/PipelineRail.tsx'), 'utf8')
    expect(src).not.toMatch(/brand-500|bg-brand|text-brand/)
  })
})
```

- [ ] **Step 2: Run scan — FAIL if brand remains**

- [ ] **Step 3: Implement density split**

1. **紧凑顶区**（`WorkbenchPage` 顶栏 + `PipelineRail`）：减小 `py`/`gap`；当前阶段可用 `shell-accent` 指示（壳层语义的阶段条允许橙）。
2. **疏朗主区**（`StageCanvas`、`ModulePanel`、生成/质量面板）：`bg-canvas` 底 + `bg-surface` 面板 + `border-border`；主按钮 `action`。
3. 全局替换 workbench/artifacts/theme 内 `brand-*` → `action-*`。
4. 更新既有测试里若断言 class 含 `brand` 的期望。

- [ ] **Step 4: Run**

Run:

```bash
cd frontend && npx vitest run src/pages/workbench.tokens.test.ts src/components/workbench -v && npm run typecheck
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/WorkbenchPage.tsx frontend/src/pages/workbench.tokens.test.ts frontend/src/components/workbench frontend/src/components/theme/ThemeMatrixPicker.tsx frontend/src/components/artifacts
git commit -m "$(cat <<'EOF'
feat(workbench): hybrid density restyle with action and shell accents

EOF
)"
```

---

### Task 10: 工具域 + 运维域页面

**Files:**
- Modify: `frontend/src/pages/ExternalReviewPage.tsx`
- Modify: `frontend/src/pages/ExternalReviewRecordsPage.tsx`
- Modify: `frontend/src/pages/ModelHubPage.tsx`
- Modify: `frontend/src/pages/LlmLogsPage.tsx`
- Modify: `frontend/src/pages/AdminConfigPage.tsx`
- Modify: `frontend/src/pages/SkillOpsPage.tsx`
- Create: `frontend/src/pages/ops-tools.tokens.test.ts`

**Interfaces:**
- Consumes: `PageShell`、表格冷雾、`action` CTA
- Produces: 六页无 indigo；日志页保持高信息密度但底色仍为冷雾（非全暗）

- [ ] **Step 1: Write scan test**

```ts
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const files = [
  'ExternalReviewPage.tsx',
  'ExternalReviewRecordsPage.tsx',
  'ModelHubPage.tsx',
  'LlmLogsPage.tsx',
  'AdminConfigPage.tsx',
  'SkillOpsPage.tsx',
]

describe('ops-tools pages tokens', () => {
  for (const file of files) {
    it(`${file} has no indigo brand classes`, () => {
      const src = readFileSync(resolve(__dirname, file), 'utf8')
      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone=\"brand\"|variant=\"brand\"/)
    })
  }
})
```

- [ ] **Step 2: Run — FAIL then fix**

- [ ] **Step 3: Restyle**

- 统一 `PageShell` + `sf-panel` / `border-border bg-surface`。
- 表格：表头 `text-ink-muted`；行 hover `bg-canvas-muted/60`；选中行可用 `bg-action/5`。
- 主按钮 `action`；可用 Task 4 的 `Table`/`Dialog` 替换手写表格壳（**可选**，若改动面过大则只换 class）。
- 不改 API hooks。

- [ ] **Step 4: Run**

Run: `cd frontend && npx vitest run src/pages/ops-tools.tokens.test.ts -v && npm run typecheck && npm run test`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ExternalReviewPage.tsx frontend/src/pages/ExternalReviewRecordsPage.tsx frontend/src/pages/ModelHubPage.tsx frontend/src/pages/LlmLogsPage.tsx frontend/src/pages/AdminConfigPage.tsx frontend/src/pages/SkillOpsPage.tsx frontend/src/pages/ops-tools.tokens.test.ts
git commit -m "$(cat <<'EOF'
feat(pages): cold-mist restyle for tools and ops domains

EOF
)"
```

---

### Task 11: 全仓清理与验收

**Files:**
- Modify: 任何仍含 `brand-` / `#6366f1` 的 `frontend/src/**`
- Modify: `docs/superpowers/specs/2026-07-17-frontend-visual-rewrite-design.md`（若需勾验收）
- Create: `frontend/src/styles/no-indigo.test.ts`

**Interfaces:**
- Consumes: Task 1–10
- Produces: 仓库级无 indigo 主色引用；验收命令全绿

- [ ] **Step 1: Write repo-wide guard test**

```ts
import { execSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'

describe('no indigo brand leftovers', () => {
  it('rg finds no brand-500 utility in src', () => {
    let out = ''
    try {
      out = execSync('rg -n "brand-500|#6366f1|bg-brand-|text-brand-" src', {
        cwd: resolveFrontendRoot(),
        encoding: 'utf8',
      })
    } catch (e) {
      // rg exit 1 = no matches
      const err = e as { status?: number; stdout?: string }
      if (err.status === 1) {
        expect(err.stdout ?? '').toBe('')
        return
      }
      throw e
    }
    expect(out).toBe('')
  })
})

function resolveFrontendRoot(): string {
  return new URL('../..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
}
```

若 Windows 上 `rg`/`import.meta.url` 路径不稳，改用 vitest + `fs` 递归扫描 `frontend/src`（实现时选可稳定跑通的写法）。

- [ ] **Step 2: Run — FAIL on leftovers, then delete/replace**

- [ ] **Step 3: Final verification commands**

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

Expected: 全部 exit 0。

手测清单（执行者勾选）：

- [ ] 登录 → 项目列表（侧栏橙 active，新建按钮海军蓝）
- [ ] 新建项目 / 设置
- [ ] 工作台阶段条 + 生成面板
- [ ] 外部评测 + 记录
- [ ] 模型管理 / LLM 日志 / 技能覆盖 / 技能运维

- [ ] **Step 4: Commit**

```bash
git add -u frontend docs/superpowers/specs/2026-07-17-frontend-visual-rewrite-design.md
git commit -m "$(cat <<'EOF'
chore(ui): purge indigo leftovers and lock visual rewrite acceptance

EOF
)"
```

---

## Self-Review

1. **Spec coverage:** token、双色、壳层、冷雾页、工作台混合、shadcn+自研、全页清单、方案 A 波次、非 Figma 门禁、验收命令均有对应 Task。
2. **Placeholder scan:** 无 TBD；Task 4 CLI 命令为明确默认；Task 11 Windows rg 提供了备用扫描策略。
3. **Type consistency:** `Button`/`Badge` 使用 `action`/`shell`；CSS 变量名与规格 §4 一致。

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-17-frontend-visual-rewrite.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 每个 Task 派新生 subagent，Task 间两阶段审查，迭代快

**2. Inline Execution** — 本会话用 executing-plans 按 Task 推进，设检查点

**Which approach?**

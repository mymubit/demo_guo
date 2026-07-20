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


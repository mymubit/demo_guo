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


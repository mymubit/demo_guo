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


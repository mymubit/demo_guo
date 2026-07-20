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


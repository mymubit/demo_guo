### Task 5: 前端 App 壳与路由（替换 studio 入口）

**Files:**
- Create: `frontend/src/app/AppShell.tsx`
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/ModelsPage.tsx`
- Create: `frontend/src/pages/LogsPage.tsx`
- Create: `frontend/src/pages/SystemPage.tsx`
- Create: `frontend/src/pages/BillingPage.tsx`
- Create: `frontend/src/pages/ProjectOverviewPage.tsx`
- Create: `frontend/src/app/router.test.tsx`
- Modify: `frontend/src/App.tsx`
- Delete or stop importing: `frontend/src/studio/**` 路由引用（目录可留到 W6 物理删除，但 `App.tsx` 不得再 import studio）

**Interfaces:**
- Consumes: Spec §2 路由表、`ProtectedRoute`、`AuthProvider`
- Produces: `/dashboard`、`/models`、`/logs`、`/system`、`/billing`、`/projects/:id` 可渲染占位

- [ ] **Step 1: 写路由测试（失败）**

`frontend/src/app/router.test.tsx`：

```tsx
import { describe, expect, it } from 'vitest'
import { V3_NAV_PATHS } from './router'

describe('v3 router paths', () => {
  it('exposes product IA paths and not studio', () => {
    expect(V3_NAV_PATHS).toEqual(
      expect.arrayContaining(['/dashboard', '/models', '/logs', '/system', '/billing']),
    )
    expect(V3_NAV_PATHS.some((p) => p.startsWith('/studio'))).toBe(false)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- src/app/router.test.tsx`  
Expected: FAIL

- [ ] **Step 3: 实现壳与路由**

`router.tsx` 导出 `V3_NAV_PATHS` 与 `V3Routes` 组件；`AppShell` 侧栏五项 + 用户退出；占位页仅标题（如「创作仪表盘」）。  
`App.tsx`：`/` → Navigate `/dashboard`；登录与 ProtectedRoute 保留；**移除**全部 `/studio`、`/governance`、`/decisions`、`/runs` 路由。

- [ ] **Step 4: 测试通过 + typecheck**

```bash
cd frontend
npm test -- src/app/router.test.tsx src/types/v3/api.test.ts
npm run typecheck
```

Expected: PASS

- [ ] **Step 5: 手工冒烟（可选）**

`npm run dev`，登录后确认侧栏五项可点，无 studio 导航。

---


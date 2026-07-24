### Task 7: W0 Minor 打磨 — 导航单一来源 + Login 文案

**Files:**
- Modify: `frontend/src/app/router.tsx`、`AppShell.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/app/router.test.tsx`（若需要）

**Interfaces:**
- Consumes: `V3_NAV_PATHS`
- Produces: `AppShell` 从单一 `V3_NAV_ITEMS`（path+label+hint+icon）导出；`V3_NAV_PATHS = V3_NAV_ITEMS.map(i => i.to)`；LoginPage 中文产品名「短剧剧本创作一体机」或「ScriptForge」，删除 Operation graph / Studio V6 旁白

- [ ] **Step 1: 改 LoginPage 文案并目视确认无 `operation`/`Studio V6` 字符串**（可加简单测试 `expect(source).not.toMatch(/Operation graph/)`）

- [ ] **Step 2: 统一导航常量**

- [ ] **Step 3:**

```bash
cd frontend
npm test -- src/app/router.test.tsx
npm run typecheck
```

---


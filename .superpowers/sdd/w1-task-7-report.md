# W1 Task 7 报告：导航单一来源 + Login 文案

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — W0 Minor 打磨 — 导航单一来源 + Login 文案  
**Commits:** none

---

## What I Implemented

### 1. 导航单一来源（`router.tsx`）

- 新增 `V3NavItem` 类型与 `V3_NAV_ITEMS`（path + label + hint + icon）
- `V3_NAV_PATHS = V3_NAV_ITEMS.map(i => i.to)` 由常量派生
- icon 从 `lucide-react` 引入，与原先 AppShell 侧栏五项一致

### 2. AppShell 消费同一来源

- 删除本地 `NAV_ITEMS` / `NavItem` 定义
- `Navigation` 改为遍历 `V3_NAV_ITEMS`（自 `./router` 导入）

### 3. LoginPage 中文产品文案

- 品牌：ScriptForge + 副标题「短剧剧本创作一体机」
- 删除：Studio V6、Operation graph、V6 runtime ready、「登录 Studio」「进入控制面」
- 替换为：「从选题到成稿，一站式短剧创作」「创作工作台」「服务就绪」「登录」「进入工作台」
- 展开 JSX 为多行，便于后续维护

### 4. 测试

- `router.test.tsx`：新增 `V3_NAV_PATHS` 与 `V3_NAV_ITEMS` 一致性断言
- `LoginPage.tokens.test.tsx`：新增无 Studio / Operation graph 源码检查

---

## Verification

**命令：**

```bash
cd frontend
npm test -- src/app/router.test.tsx src/pages/LoginPage.tokens.test.tsx
npm run typecheck
```

**结果：** PASS

```
 ✓ src/pages/LoginPage.tokens.test.tsx (2 tests)
 ✓ src/app/router.test.tsx (2 tests)

 Test Files  2 passed (2)
      Tests  4 passed (4)

typecheck: tsc -b --pretty false → exit 0
```

---

## Concerns

1. `frontend/index.html` 标题仍为「ScriptForge Studio · V6」，不在本 Task 文件清单内，W1 Task 8 验收时可一并改。
2. 旧 Studio 路由（`frontend/src/studio/*`）仍存在但未挂 V3 路由，与 W0 硬切一致，无回归风险。

---

## Files Touched

- `frontend/src/app/router.tsx`
- `frontend/src/app/AppShell.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/app/router.test.tsx`
- `frontend/src/pages/LoginPage.tokens.test.tsx`
- `.superpowers/sdd/w1-task-7-report.md`（本文件）

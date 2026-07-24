# W0 Task 5 报告：前端 App 壳与路由（替换 studio 入口）

**Status:** DONE  
**Date:** 2026-07-22  
**Task:** ScriptForge V3 W0 — 前端 App 壳与路由（替换 studio 入口）  
**Commits:** none（按指令未提交）

---

## Note on Brief

`.superpowers/sdd/w0-task-5-brief.md` 当时不存在；按  
`docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md` Task 5 与用户下发 Interfaces 执行。

---

## What I Implemented

### 1. TDD 流程（严格 RED → GREEN）

| 阶段 | 命令 | 结果 |
|------|------|------|
| RED | `npm test -- src/app/router.test.tsx` | **FAIL** — `./router` 模块不存在 |
| GREEN | `npm test -- src/app/router.test.tsx src/types/v3/api.test.ts` | **PASS** — 2 files / 2 tests |
| typecheck | `npm run typecheck` | **PASS** |

### 2. RED 证据

```
 FAIL  src/app/router.test.tsx [ src/app/router.test.tsx ]
Error: Failed to resolve import "./router" from "src/app/router.test.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: C:/Users/99193/Desktop/demo_guo/frontend/src/app/router.test.tsx:2:29
  1  |  import { describe, expect, it } from "vitest";
  2  |  import { V3_NAV_PATHS } from "./router";
     |                                ^

 Test Files  1 failed (1)
      Tests  no tests
```

### 3. GREEN 证据

```
 ✓ src/types/v3/api.test.ts (1 test) 2ms
 ✓ src/app/router.test.tsx (1 test) 1ms

 Test Files  2 passed (2)
      Tests  2 passed (2)
```

### 4. typecheck 证据

```
> scriptforge-workbench@1.0.0 typecheck
> tsc -b --pretty false

（exit 0，无错误输出）
```

### 5. 新建 / 修改文件

| 路径 | 操作 | 内容 |
|------|------|------|
| `frontend/src/app/router.test.tsx` | 新建 | V3_NAV_PATHS 含 IA 路径且不含 `/studio` |
| `frontend/src/app/router.tsx` | 新建 | 导出 `V3_NAV_PATHS`、`V3Routes` |
| `frontend/src/app/AppShell.tsx` | 新建 | 侧栏五项中文导航 + 用户退出 |
| `frontend/src/pages/DashboardPage.tsx` | 新建 | 占位「创作仪表盘」 |
| `frontend/src/pages/ModelsPage.tsx` | 新建 | 占位「模型配置」 |
| `frontend/src/pages/LogsPage.tsx` | 新建 | 占位「执行日志」 |
| `frontend/src/pages/SystemPage.tsx` | 新建 | 占位「系统配置」 |
| `frontend/src/pages/BillingPage.tsx` | 新建 | 占位「套餐」 |
| `frontend/src/pages/ProjectOverviewPage.tsx` | 新建 | 占位「项目概览」 `/projects/:id` |
| `frontend/src/App.tsx` | 修改 | 仅挂 `AuthProvider` + `V3Routes`；**零** studio import |
| `frontend/src/pages/LoginPage.tsx` | 修改 | 登录后跳转 `/dashboard`（原 `/studio`） |

### 6. 路由契约核对

| 要求 | 结果 |
|------|------|
| `/` → `/dashboard` | ✓ `Navigate` |
| Global: `/dashboard`, `/models`, `/logs`, `/system`, `/billing`, `/login` | ✓ |
| Project: `/projects/:id` overview placeholder | ✓ |
| 移除 `/studio`, `/governance`, `/decisions`, `/runs` | ✓ App.tsx / router 无引用 |
| 保留 AuthProvider / ProtectedRoute / LoginPage / http/auth | ✓ |
| `studio/**` 可留盘但不被 App 导入 | ✓ |
| 导出 `V3_NAV_PATHS` | ✓ |
| 占位页无 `operation.*` 术语 | ✓ |
| 创作者向中文标签 | ✓ |

---

## Concerns

1. **Brief 缺失**：`w0-task-5-brief.md` 未落盘；实现依据 plan Task 5。
2. **LoginPage 文案仍偏 Studio V6**：跳转路径已改 `/dashboard`，但页面标题/旁白仍写「Studio / 控制面」；W0 未要求改文案，留给后续视觉重写。
3. **`studio/**` 仍在磁盘**：按 W0 纪律仅断路由引用；物理删除留给 W6。
4. **项目内子路由未挂**：`/projects/:id/topic|blueprint|…` 属后续波次；W0 仅概览占位。
5. **通配重定向**：未登录访问 `*` 会进 ProtectedRoute 再落到 `/dashboard` 保护链；已认证未知路径 → `/dashboard`。行为可接受，若需更细 404 可后续加。

---

## Verification Checklist

- [x] RED：`router.test.tsx` 因模块缺失失败
- [x] GREEN：`router.test.tsx` + `api.test.ts` 全绿
- [x] `npm run typecheck` 全绿
- [x] App.tsx 无 studio / governance / decisions / runs
- [x] 未 git commit
- [x] 未引入新第三方库

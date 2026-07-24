# 项目向导工作台 W1 Implementation Plan

> **For agentic workers:** 按任务逐步执行；未要求不 commit。

**Goal:** 嵌套 `ProjectWorkbenchLayout`；仪表盘直达当前阶段；原概览迁到 `/settings`。

**Architecture:** React Router 嵌套路由；左轨用 stage→path 映射；index 按 `project.stage` 重定向。

**Tech Stack:** React Router 6、React Query、既有 PageShell/阶段页。

**Spec:** `docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md` §5 W1

## Global Constraints

- 不暴露 operation/recipe ID
- 不改后端 stage 机
- 不引入新 npm 依赖
- 中文 UI

## File map

| 文件 | 职责 |
|------|------|
| `frontend/src/pages/projectStagePaths.ts` | stage↔path、prev/next |
| `frontend/src/pages/ProjectWorkbenchLayout.tsx` | 左轨 + 顶栏 + Outlet |
| `frontend/src/app/router.tsx` | 嵌套路由 |
| `frontend/src/pages/dashboard/ProjectCard.tsx` | 链到当前阶段 |
| `frontend/src/pages/ProjectOverviewPage.tsx` | 文案改为「项目设置」 |
| 相关 `*.test.tsx` | 路由与卡片链接 |

---

### Task 1: stage path 工具

**Files:** Create `projectStagePaths.ts` + `projectStagePaths.test.ts`

- `STAGE_PATH_ORDER`、`pathForStage(id, stage)`、`stageFromPathSegment(seg)`、`adjacentStage(stage, dir)`
- writing → `editor`

### Task 2: WorkbenchLayout

**Files:** `ProjectWorkbenchLayout.tsx` + test

- `getProject`；左轨六步 NavLink；顶栏标题、上一步/下一步、设置链接；`<Outlet />`
- 加载/错误态

### Task 3: 路由嵌套

**Files:** `router.tsx`

```
/projects/:id → WorkbenchLayout
  index → StageRedirect
  settings → ProjectOverviewPage
  topic|blueprint|episodes|editor|quality|delivery → 原页面
```

### Task 4: 仪表盘入口

**Files:** `ProjectCard.tsx`、`DashboardPage` create 已跳 topic 保持；测卡片 `href` 含当前 stage 路径

### Task 5: 基线

写 `docs/superpowers/baselines/2026-07-24-project-workbench-w1-acceptance.md`

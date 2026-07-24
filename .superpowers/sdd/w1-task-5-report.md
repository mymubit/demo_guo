# W1 Task 5 报告：仪表盘接真 + 新建项目

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 仪表盘接真 + 新建项目  
**Commits:** none

---

## What I Implemented

### 1. `DashboardPage.tsx`

- TanStack Query：`listProjects()` 拉取列表（`queryKey: ['v3', 'projects']`）
- 项目卡：标题、创作来源中文（原创/改编）、阶段中文（`STAGE_LABEL`）、更新时间；点击进入 `/projects/:id`
- 禁止以 UUID 作主文案
- 「新建项目」打开对话框；创建成功后 `navigate(/projects/${id})`
- 空状态中文：「还没有项目」

### 2. `CreateProjectDialog.tsx`（可选拆分）

- Radix `Dialog` + `Input` + `Button`
- 字段：项目标题、创作来源（original / adapt）
- 提交文案：「创建并进入」

### 3. `DashboardPage.test.tsx`

Mock `@/services/v3/projects`，覆盖：

1. 有项目时渲染标题与「原创 · 选题定调」
2. 空列表显示「还没有项目」
3. user-event 打开对话框 → 提交 → 调用 `createProject` → 导航至项目概览占位

---

## TDD: RED → GREEN

### Step 1: RED

**命令：**

```bash
cd frontend
npm test -- src/pages/DashboardPage.test.tsx
```

**结果：** FAIL（3 failed）

占位页仍显示「占位页：后续接入项目列表与新建入口。」，无项目标题 / 空状态 / 新建按钮。符合预期。

### Step 2: 实现

- 修改 `DashboardPage.tsx`
- 新建 `dashboard/CreateProjectDialog.tsx`

### Step 3: GREEN

**命令：**

```bash
cd frontend
npm test -- src/pages/DashboardPage.test.tsx src/services/v3/projects.test.ts
npm run typecheck
```

**结果：** PASS

```
 ✓ src/services/v3/projects.test.ts (3 tests)
 ✓ src/pages/DashboardPage.test.tsx (3 tests)

 Test Files  2 passed (2)
      Tests  6 passed (6)

typecheck: tsc -b --pretty false → exit 0
```

---

## Concerns

1. Task 6 才做「显示已归档」与卡片归档入口；本任务列表固定 `listProjects()`（不含归档）。
2. 创建失败时对话框内展示 `formatApiError`；未单独覆盖错误路径单测。
3. 测试中有 React Router v7 future flag 警告（既有模式），不影响断言。

---

## Files Touched

- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/DashboardPage.test.tsx`（new）
- `frontend/src/pages/dashboard/CreateProjectDialog.tsx`（new）
- `.superpowers/sdd/w1-task-5-report.md`（本文件）

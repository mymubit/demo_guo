# W1 Task 6 报告：项目概览 + 归档入口

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 项目概览 + 归档入口  
**Commits:** none

---

## What I Implemented

### 1. `/projects/:id/topic` 占位路由

- 新增 `TopicPage.tsx`：中文标题「选题定调」，无 operation 术语
- `router.tsx` 注册 `/projects/:id/topic`

### 2. `ProjectOverviewPage.tsx`

- `getProject(id)` 拉取详情
- 展示：标题、创作来源、阶段、进度
- 主 CTA「去选题定调」→ `/projects/:id/topic`
- 「归档项目」→ 确认对话框 → `archiveProject` → `navigate('/dashboard')`

### 3. `DashboardPage.tsx`

- 「显示已归档」checkbox → `listProjects(true)`（queryKey 含 `includeArchived`）
- 项目卡「归档」按钮 + 确认对话框；已归档卡隐藏归档按钮并标注「已归档」

### 4. 共享

- `projectLabels.ts`：`STAGE_LABEL` / `ENTRY_LABEL`（Dashboard 与 Overview 共用）
- `ArchiveConfirmDialog.tsx`：归档确认对话框

### 5. 测试

- `ProjectOverviewPage.test.tsx`：详情展示、CTA 导航、归档后回仪表盘
- `DashboardPage.test.tsx`：增补「显示已归档」与卡片归档

---

## TDD: RED → GREEN

### Step 1: RED

**命令：**

```bash
cd frontend
npm test -- src/pages/ProjectOverviewPage.test.tsx src/pages/DashboardPage.test.tsx
```

**结果：** FAIL（5 failed | 3 passed）— 概览仍为占位；仪表盘无归档开关/卡片归档。符合预期。

### Step 2: 实现

- `TopicPage.tsx`、`ArchiveConfirmDialog.tsx`、`projectLabels.ts`
- 修改 `ProjectOverviewPage.tsx`、`DashboardPage.tsx`、`router.tsx`
- 测试文件如上

### Step 3: GREEN

**命令：**

```bash
cd frontend
npm test -- src/pages/ProjectOverviewPage.test.tsx src/pages/DashboardPage.test.tsx
npm run typecheck
```

**结果：** PASS

```
 ✓ src/pages/ProjectOverviewPage.test.tsx (3 tests)
 ✓ src/pages/DashboardPage.test.tsx (5 tests)

 Test Files  2 passed (2)
      Tests  8 passed (8)

typecheck: tsc -b --pretty false → exit 0
```

---

## Concerns

1. CTA「去选题定调」用 styled `Link`（`Button` 无 `asChild`），视觉对齐 action 按钮。
2. TopicPage 仅为 W1 防死链占位，无真实选题工作台。
3. React Router v7 future flag 警告（既有模式），不影响断言。

---

## Files Touched

- `frontend/src/app/router.tsx`
- `frontend/src/pages/TopicPage.tsx`（new）
- `frontend/src/pages/ProjectOverviewPage.tsx`
- `frontend/src/pages/ProjectOverviewPage.test.tsx`（new）
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/DashboardPage.test.tsx`
- `frontend/src/pages/ArchiveConfirmDialog.tsx`（new）
- `frontend/src/pages/projectLabels.ts`（new）
- `.superpowers/sdd/w1-task-6-report.md`（本文件）

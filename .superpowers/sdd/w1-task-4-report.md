# W1 Task 4 报告：前端 v3 projects 客户端 + 类型补全

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 前端 v3 projects 客户端 + 类型补全  
**Commits:** none

---

## What I Implemented

### 1. 类型（`frontend/src/types/v3/domain.ts`）

- `ProjectSummary` 增加 `archived_at?: string | null`
- 新增 `CommandRunStatus`、`CommandRunSummary`（对齐 OpenAPI `CommandRun`）

### 2. 导出（`frontend/src/types/v3/api.ts`）

- 导出 `CommandRunStatus`、`CommandRunSummary`

### 3. 服务（`frontend/src/services/v3/projects.ts`）

基于 `@/services/http` 的 `http.get` / `http.post`（envelope 已解包）：

| 函数 | 方法 | 路径 |
|------|------|------|
| `listProjects(includeArchived?)` | GET | `/api/v3/projects/`（`includeArchived=true` 时 `params: { include_archived: 1 }`） |
| `createProject(body)` | POST | `/api/v3/projects/` |
| `getProject(id)` | GET | `/api/v3/projects/{id}/` |
| `archiveProject(id)` | POST | `/api/v3/projects/{id}/archive/` |
| `dispatchCommand(input)` | POST | `/api/v3/commands/` |

列表响应从 `{ items: ProjectSummary[] }` 解包为 `ProjectSummary[]`。

### 4. 测试（`frontend/src/services/v3/projects.test.ts`）

Vitest + `vi.mock('@/services/http')`，覆盖：

1. `listProjects()` 默认 GET `/api/v3/projects/`，无 `include_archived` 参数  
2. `listProjects(true)` 传递 `params: { include_archived: 1 }`  
3. `archiveProject(id)` POST `/api/v3/projects/{id}/archive/`

---

## TDD: RED → GREEN

### Step 1–2: RED（失败测试）

**命令：**

```bash
cd frontend
npm test -- src/services/v3/projects.test.ts src/types/v3/api.test.ts
```

**结果：** FAIL

```
Error: Failed to resolve import "./projects" from "src/services/v3/projects.test.ts". Does the file exist?
```

符合预期：`projects.ts` 与类型补全尚未实现。

### Step 3: 实现

- 修改 `domain.ts`、`api.ts`
- 新建 `services/v3/projects.ts`

### Step 4: GREEN

**命令：**

```bash
cd frontend
npm test -- src/services/v3/projects.test.ts src/types/v3/api.test.ts
```

**结果：** PASS

```
 ✓ src/types/v3/api.test.ts (1 test)
 ✓ src/services/v3/projects.test.ts (3 tests)

 Test Files  2 passed (2)
      Tests  4 passed (4)
```

---

## Concerns

1. `createProject` / `getProject` / `dispatchCommand` 尚无独立单测；Task 5/6 集成 Dashboard / 概览时再补 mock 覆盖即可。  
2. `POST /projects/` 失败时后端可能返回 `{ command_run }` + HTTP 400；当前 `createProject` 未区分该形态，与 W0 成功路径一致。  
3. `dispatchCommand` 的 `command_type` 仍为 `string`；后续可按 `ProductCommandType` 收紧输入类型。

---

## Files Touched

- `frontend/src/types/v3/domain.ts`
- `frontend/src/types/v3/api.ts`
- `frontend/src/services/v3/projects.ts`（new）
- `frontend/src/services/v3/projects.test.ts`（new）
- `.superpowers/sdd/w1-task-4-report.md`（本文件）

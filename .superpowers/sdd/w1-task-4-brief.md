### Task 4: 前端 v3 projects 客户端 + 类型补全

**Files:**
- Create: `frontend/src/services/v3/projects.ts`
- Create: `frontend/src/services/v3/projects.test.ts`
- Modify: `frontend/src/types/v3/domain.ts`（`archived_at?: string | null`；`CommandRunSummary`）
- Modify: `frontend/src/types/v3/api.ts`（导出）

**Interfaces:**
- Consumes: `http` 模块现有 `get/post`（查看 `frontend/src/services/http.ts` 导出的请求函数名，按仓库实际使用；若仅 axios 封装则用同一套）
- Produces:
  - `listProjects(includeArchived?: boolean): Promise<ProjectSummary[]>`
  - `createProject(body: CreateProjectRequest): Promise<ProjectSummary>`
  - `getProject(id: string): Promise<ProjectSummary>`
  - `archiveProject(id: string): Promise<ProjectSummary>`
  - `dispatchCommand(input: { command_type: string; payload: Record<string, unknown>; idempotency_key?: string }): Promise<{ command_run: CommandRunSummary; project?: ProjectSummary }>`

- [ ] **Step 1: 读 `http.ts` 确认导出 API（`request` / `http.get` 等），按现有模式写 clients**

- [ ] **Step 2: 写 `projects.test.ts`**（用 vitest mock axios/http），至少覆盖：
  - `listProjects` 请求 `/api/v3/projects/` 且默认无 `include_archived`
  - `archiveProject` POST `/api/v3/projects/{id}/archive/`

- [ ] **Step 3: 实现并跑通**

```bash
cd frontend
npm test -- src/services/v3/projects.test.ts src/types/v3/api.test.ts
```

Expected: PASS

---


# W0 Task 2 报告：OpenAPI 契约（项目列表 + 命令信封）

**Status:** DONE  
**Date:** 2026-07-22  
**Task:** ScriptForge V3 W0 — OpenAPI 契约（项目列表 + 命令信封）

---

## What I Implemented

### 1. `docs/contracts/v3/openapi.yaml`

- 按 brief Step 1 逐字落盘最小 OpenAPI 3.0.3 契约。
- 覆盖 W0 所需路径：`GET/POST /projects/`、`GET /projects/{project_id}/`、`GET /billing/plans/`。
- 定义统一响应信封 `Envelope`（`required: [code, message, data]`）及项目/套餐相关 schema。
- 认证：`bearerAuth`（JWT Bearer）。

---

## Verification Performed

### Step 2 人工核对（路径与前缀）

| 检查项 | 预期 | 实际 | 结果 |
|--------|------|------|------|
| server 前缀 | `/api/v3` | `/api/v3` | ✓ |
| 项目列表 | `/projects/`（尾斜杠） | `/projects/` | ✓ |
| 项目详情 | `/projects/{project_id}/`（尾斜杠） | `/projects/{project_id}/` | ✓ |
| 套餐壳 | `/billing/plans/`（尾斜杠） | `/billing/plans/` | ✓ |
| 与 Spec §4.1 对齐 | `/api/v3/projects/`、`/api/v3/billing/plans/` | server + path 拼接一致 | ✓ |
| 响应信封 | `{ code, message, data }` | `Envelope.required: [code, message, data]` | ✓ |

### YAML 可解析性

使用 `py -c "yaml.safe_load(...)"` 解析成功；paths 共 3 条，operationId 为 `listProjects`、`createProject`、`getProject`、`listBillingPlans`。

### 与 Task 1 衔接

- `commands.md` 已标注套餐壳为 REST 只读 `/api/v3/billing/plans/`，与本 OpenAPI 路径一致。
- `create_project` command 对应 `POST /projects/` REST 创建；W0 OpenAPI 未定义 command 提交端点（后续里程碑追加）。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `docs/contracts/v3/openapi.yaml` | 新建 |
| `.superpowers/sdd/w0-task-2-report.md` | 新建（本报告） |

未修改 backend/frontend 应用代码；未执行 git commit。

---

## Self-Review

- YAML 内容与 `.superpowers/sdd/w0-task-2-brief.md` Step 1 代码块逐字对齐。
- 所有 path 均为 Django 风格尾斜杠；`ProjectStage` enum 与 Spec 阶段语义一致。
- `ProjectSummary` 必填字段与 Task 4 冒烟测试预期字段兼容（`id`、`title`、`entry_type`、`stage`、`updated_at`）。
- W0 范围 intentionally 不含 command envelope path/schema；任务标题「命令信封」指共享 `Envelope` schema，非 command API。

---

## Concerns

1. **W0 范围有限**：本文件仅含 projects + billing 只读壳；Spec §4.1 其余 REST（`/system/`、`/models/`、`/logs/`、command 提交）留待后续 Task/里程碑追加，符合 brief「最小 OpenAPI」定位。
2. **POST 创建项目 HTTP 200**：契约指定 200 而非 201；与现有 `api_response` 信封习惯一致，Task 4 实现时需对齐。
3. **command_type 未入 OpenAPI**：Task 1 的 15 条 command 枚举尚未映射为 OpenAPI schema/path；Task 3 TS 类型与后续里程碑需引用 `commands.md` 直至 command API 契约追加。

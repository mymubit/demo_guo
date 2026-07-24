# W0 Task 3 报告：前端 TS 类型与契约测试

**Status:** DONE  
**Date:** 2026-07-22  
**Task:** ScriptForge V3 W0 — 前端 TS 类型与契约测试

---

## What I Implemented

### 1. TDD 流程（严格 RED → GREEN）

| 阶段 | 命令 | 结果 |
|------|------|------|
| RED | `cd frontend; npm test -- src/types/v3/api.test.ts` | **FAIL** — `./commands` 模块不存在 |
| GREEN | 同上（实现类型后） | **PASS** — 1 test passed |

### 2. RED 证据

```
 FAIL  src/types/v3/api.test.ts [ src/types/v3/api.test.ts ]
Error: Failed to resolve import "./commands" from "src/types/v3/api.test.ts". Does the file exist?
  File: .../frontend/src/types/v3/api.test.ts:2:38
  import { PRODUCT_COMMAND_TYPES } from "./commands";

 Test Files  1 failed (1)
      Tests  no tests
   Duration  932ms
```

### 3. GREEN 证据

```
 ✓ src/types/v3/api.test.ts (1 test) 2ms

 Test Files  1 passed (1)
      Tests  1 passed (1)
   Duration  921ms
```

### 4. 新建文件

| 路径 | 内容 |
|------|------|
| `frontend/src/types/v3/commands.ts` | `PRODUCT_COMMAND_TYPES`（15 条 snake_case）+ `ProductCommandType` |
| `frontend/src/types/v3/domain.ts` | `ProjectEntryType`、`ProjectStage`、`ProjectSummary`、`CreateProjectRequest`、`BillingPlan` |
| `frontend/src/types/v3/api.ts` | 重导出 domain/commands 类型 + `ApiEnvelope<T>` |
| `frontend/src/types/v3/api.test.ts` | 契约测试：含 `generate_topic_brief`/`prepare_delivery`，不含 `create-project-brief` |

---

## Contract Alignment

### 与 `docs/contracts/v3/commands.md` 对齐

| 检查项 | 预期 | 实际 | 结果 |
|--------|------|------|------|
| command 数量 | 15 | 15 | ✓ |
| 命名风格 | snake_case | 全部 snake_case | ✓ |
| 不含 skills ID | 无 `create-project-brief` 等 | 测试断言 `not.toContain('create-project-brief')` | ✓ |
| 首尾 command | `create_project` … `test_model_provider` | 与 commands.md 表一致 | ✓ |

### 与 OpenAPI / domain 对齐

- `ProjectEntryType`：`original` \| `adapt` — 与 openapi `ProjectEntryType` enum 一致。
- `ProjectStage`：`topic` \| `blueprint` \| `episodes` \| `writing` \| `quality` \| `delivery` — 与 openapi `ProjectStage` enum 一致。
- `ProjectSummary`、`CreateProjectRequest`、`BillingPlan` — 字段与 Task 2 `openapi.yaml` schema 对齐。
- `ApiEnvelope<T>` — 对应 OpenAPI `Envelope`（`code`、`message`、`data`）。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `frontend/src/types/v3/commands.ts` | 新建 |
| `frontend/src/types/v3/domain.ts` | 新建 |
| `frontend/src/types/v3/api.ts` | 新建 |
| `frontend/src/types/v3/api.test.ts` | 新建 |
| `.superpowers/sdd/w0-task-3-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

- 类型文件内容与 `.superpowers/sdd/w0-task-3-brief.md` Step 3 代码块逐字对齐。
- TDD 顺序正确：先写测试 → RED → 实现 → GREEN。
- `PRODUCT_COMMAND_TYPES` 与 commands.md 15 条一一对应，无遗漏、无多余。
- ESLint 对新建文件无新增诊断。

---

## Concerns

1. **测试覆盖较窄**：当前仅 1 条断言验证关键 command 存在性与 skills ID 隔离；未断言完整 15 条枚举或 `ProductCommandType` 与数组双向一致（brief 未要求，后续可增强）。
2. **command API 类型未定义**：W0 仅导出 `ProductCommandType` 常量；command 请求/响应 payload 类型留待 command OpenAPI path 追加后补全。
3. **pages/services 尚未引用**：类型已就绪供后续 W0 页面与 services 导入，当前无消费方改动。

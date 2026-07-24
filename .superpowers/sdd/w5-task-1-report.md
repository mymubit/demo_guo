# W5 Task 1 报告：契约 + OpenAPI 补洞 + TS 类型

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — 契约 / OpenAPI（含 W4 paths）/ TS 类型（无 views）  
**Commits:** none（用户未要求）  
**Brief:** `.superpowers/sdd/w5-task-1-brief.md` 当时不存在；按计划 `docs/superpowers/plans/2026-07-23-drama-website-v3-w5-system-models-logs.md` Task 1 + Global 产品语义执行。

---

## What I Implemented

### 1. OpenAPI `docs/contracts/v3/openapi.yaml`

**W4 补洞 paths：**

- `GET /projects/{id}/quality/`
- `POST …/quality/score|compliance|accept|revise/`
- `GET /projects/{id}/delivery/`
- `POST …/delivery/prepare/`
- 配套 `QualityAcceptRequest` / `QualityReviseRequest`

**W5 新 paths + schemas：**

- `GET/PUT /system/config/` → `SystemConfigState` / `SystemConfigPutRequest`
- `GET/POST /models/providers/`、`GET/PATCH/DELETE …/{provider_id}/`、`activate/`、`test/`
- `GET/PUT /models/role-mappings/`
- `GET /logs/runs/`、`GET /logs/runs/{run_id}/`、`GET /logs/calls/{call_id}/`
- `ModelProvider`（仅 `api_key_set`）、`ModelProviderWrite`（`api_key` writeOnly）、`RoleModelMapping`、`LogRun`、`LogCall`

### 2. `commands.md`

- `test_model_provider`：**异步 = 否**（同步 live）
- 新增「模型试连约定（W5）」：payload `{ provider_id }`、写 `CONNECTIVITY_TEST`、可走 REST test

### 3. 前端类型

- `domain.ts`：`SystemConfig*`、`ModelProvider*`、`ROLE_MODEL_KEYS` / `RoleModelMapping*`、`LogCall` / `LogRun` / `LogRunList`
- `api.ts`：重导出 W4 Quality/Delivery + W5 类型与 `ROLE_MODEL_KEYS`

### 4. 测试 `frontend/src/types/v3/api.test.ts`

契约断言：W4/W5 OpenAPI paths、schema 存在、Provider 响应无 `api_key`、角色键表、类型 key 形状。

---

## TDD: RED → GREEN

### Step 1: RED

```bash
cd frontend
npm test -- src/types/v3/api.test.ts
```

失败：缺 OpenAPI paths / schemas；`ROLE_MODEL_KEYS` undefined。

### Step 2–3: 实现 + GREEN

同命令复跑 → **8 tests passed**；`npm run typecheck` → OK。

---

## Self-Review

- [x] 仅契约/类型；无 views / services / migrations
- [x] W4 quality/delivery paths 已挂到既有 schemas
- [x] `test_model_provider` 同步 live 写入 commands.md
- [x] Provider 响应契约无明文 `api_key`
- [x] 未引入 v6_* / 新依赖
- [x] 未 commit

### Concerns（非阻塞）

1. **brief 缺失**：按 W5 计划 Task 1 Global 语义落地；若 brief 后续补发字段差异需对齐。
2. **`SystemConfigOverlay.additionalProperties: false`**：文档层收紧允许键；实现层「忽略并 warn」可在 Task 2/3 放宽校验而不改公开字段语义。
3. **Logs 列表分页**：契约用 `limit/offset`（≤50）；后端 Task 6 若沿用其他分页需保持信封字段一致。

### 风险

低。纯契约/类型，无运行时入口变更。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `docs/contracts/v3/openapi.yaml` | W4 paths + W5 system/models/logs |
| `docs/contracts/v3/commands.md` | test_model_provider 同步 live |
| `frontend/src/types/v3/domain.ts` | W5 域类型 |
| `frontend/src/types/v3/api.ts` | 重导出 |
| `frontend/src/types/v3/api.test.ts` | 契约 smoke |
| `.superpowers/sdd/w5-task-1-report.md` | 本报告 |

---

## Follow-ups

- Task 2：`V3SystemConfigRevision` + resolver  
- Task 4–6：Models/Logs REST 与试连 live 实现对齐本契约

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 |
|--------|------|
| W4 quality/delivery OpenAPI paths | ✅ 7 paths + `QualityAcceptRequest` / `QualityReviseRequest` |
| W5 system/models/logs schemas+paths | ✅ 全部路径与 schema；`ModelProvider` 仅 `api_key_set` |
| TS types (`domain.ts` / `api.ts`) | ✅ 与 OpenAPI 对齐；8 角色键完整 |
| `test_model_provider` 同步 live（`commands.md`） | ✅ 表列异步=否 + W5 约定段 |
| 契约 smoke | ✅ `api.test.ts` 8/8；`npm run typecheck` 绿 |
| 范围 | ✅ 仅契约/类型，无 views |

**Minor（Task 6 前补齐即可）：** `/logs/runs/` 缺时间范围 query（计划 Global 语义）；`SystemConfigOverlay.additionalProperties: false` 与实现层「忽略并 warn」需在 Task 2/3 对齐策略。

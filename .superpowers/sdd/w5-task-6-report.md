# W5 Task 6 报告：LLM 日志挂 V3 run + Logs REST

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — `DramaLlmCallLog` 挂 `V3CommandRun` + `/api/v3/logs/**`  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-6-brief.md`

---

## What I Implemented

### 1. Model + Migration `0019_dramallmcalllog_v3_fks`

- `DramaLlmCallLog.v3_command_run` → `V3CommandRun`（nullable SET_NULL）
- `DramaLlmCallLog.v3_project` → `V3Project`（nullable SET_NULL）
- 索引：`(v3_command_run, -created_at)`、`(v3_project, -created_at)`
- 旧 `project` / `generation_job` 保留

### 2. Context + 写日志

- `LlmCallContext` / `llm_call_scope` 增加 `v3_command_run_id`、`v3_project_id`
- `LlmCallLogService.record` 从 context（或显式参数）解析并落库 V3 FK
- 新增 `serialize_v3_call(full=)`：run 详情截断；call 详情全量；永不含 `api_key`

### 3. Executor 埋点

- `execute_generation` 在调用 `llm_call` / `LlmProvider` 前进入 `llm_call_scope`
- 注入 `v3_command_run_id`、`v3_project_id`、agent `role`、`actor=owner.username`

### 4. Logs REST

| Method | Path | 行为 |
|--------|------|------|
| GET | `/api/v3/logs/runs/` | owner 隔离；筛 `project_id`/`status`/`command_type`/`created_after`/`created_before`；`limit`≤50 |
| GET | `/api/v3/logs/runs/{run_id}/` | run + 关联 calls（截断正文） |
| GET | `/api/v3/logs/calls/{call_id}/` | 全量快照；非 owner → 404 |

### 5. 测试 `test_v3_logs_api.py`（6）

- mock generate → call 挂到 run/project
- 列表 owner 隔离 + 过滤 + limit cap
- run 详情含 calls；call 详情全量且无密钥
- 跨用户 404

---

## Verification

```bash
cd backend
$env:DRAMA_SKILLS_ROOT='c:\Users\99193\Desktop\demo_guo\drama-skills'
py -3 manage.py test apps.drama.tests.test_v3_logs_api apps.drama.tests.test_llm_call_log apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_provider_test -v 1 --settings=config.settings.sqlite_test
```

**结果：46/46 OK**（logs 6 + llm_call_log 6 + skills_bridge 26 + provider_test 8）

---

## Self-Review

- [x] Executor 注入 v3 ids 后再调 LLM
- [x] FK 可空；旧字段保留
- [x] Logs API owner 隔离；limit≤50
- [x] 响应无 api_key
- [x] 无 v6_* / 无新依赖 / 未 commit

### Concerns（非阻塞）

1. **`test_model_provider` 试连日志未挂 run**：试连走 `provider_test._record_log`，未设 `llm_call_scope`；本任务 brief 只要求 executor。若日志页要展示试连，需后续在 `run_test_model_provider_command` 注入 context。
2. **`purpose` 统一 `artifact_generation`**：score/compliance 生成也写同 purpose；若需区分可按 command_type 映射。
3. **OpenAPI 未列 `created_after`/`created_before`**：实现已支持；契约可在后续补参数。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 |
|--------|------|
| `DramaLlmCallLog` v3 FK（nullable SET_NULL + 索引） | ✅ `0019` + model |
| `llm_call_context` / `record` 解析 v3 ids | ✅ |
| Executor `llm_call_scope` 先于 LLM 调用 | ✅ `executor.py:128-135` |
| Logs REST owner 隔离 + limit≤50 | ✅ 三端点 + 跨用户 404 |
| mock generate → call 挂 run/project | ✅ `test_generate_links_llm_call_to_v3_run` |

**验证：** 独立复跑 `test_v3_logs_api` 6/6 OK。

**备注（非阻塞）：** `created_after`/`created_before` 已实现但未单测；试连日志未挂 run（report 已说明）；OpenAPI 未补日期参数。

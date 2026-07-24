# W5 Task 5 报告：test_model_provider live + 角色映射进 executor

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W5 — SYNC `test_model_provider` + `V3RoleModelMapping` 覆盖 active  
**Commits:** none（用户明确要求不 commit）  
**Brief:** `.superpowers/sdd/w5-task-5-brief.md`

---

## What I Implemented

### 1. 命令类型（SYNC）

- `types.py`：`test_model_provider` 移出 `ASYNC_STUB` → 新集合 `SYNC_PROVIDER_TEST_COMMANDS`
- `ASYNC_STUB_COMMANDS` 置空（W5 起无剩余 stub）

### 2. `orchestrator/provider_test.py`

- `test_provider_connectivity(provider_id, actor)`：对齐 studio 行为，`GET {base_url}/models` + Bearer
- 成功/失败均写 `CONNECTIVITY_TEST`（`LlmCallLogService.record`）；永不记录 api_key
- 中文错误：缺配置 / 不存在 / HTTP 失败 / 网络异常
- `run_test_model_provider_command`：同步创建 `V3CommandRun`，payload `{ provider_id }`

### 3. Dispatcher

- `SYNC_PROVIDER_TEST_COMMANDS` → `run_test_model_provider_command`

### 4. 角色映射 → executor

- `LlmConfigService.resolve_for_role(role_key)`：有 `V3RoleModelMapping` 则用映射 provider（可覆盖 temp/max_tokens）；无行则 `resolve()`（active）
- `LlmProvider.chat_completion(..., config=)`：支持临时覆盖 `ResolvedLlmConfig`
- `executor._default_llm_call(prompt, role=)` + `execute_generation` 按 `recipe.role` 注入

### 5. Optional REST

- `POST /api/v3/models/providers/{id}/test/` → 同一 `test_provider_connectivity`

### 6. 测试 `test_v3_provider_test.py`（8）

- 同步成功 + 写日志（mock `requests.get`）
- HTTP 失败 → `failed` + 中文 + ERROR 日志
- 缺 `provider_id` → failed（非 unsupported）
- REST test 端点
- 映射优先 / fall back active / executor 传 `config`

回归：`test_v3_orchestrator`、`test_v3_projects_crud` stub 断言已改为 live 语义。

---

## Verification

```bash
cd backend
$env:DRAMA_SKILLS_ROOT='c:\Users\99193\Desktop\demo_guo\drama-skills'
py -3 manage.py test apps.drama.tests.test_v3_provider_test apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_models_api -v 1 --settings=config.settings.sqlite_test
```

**结果：23/23 OK**（含 provider 8 + orch + projects + models）

---

## Self-Review

- [x] SYNC live；mock HTTP；无真实外网
- [x] CONNECTIVITY_TEST 成功/失败均写
- [x] 映射覆盖 active；无映射用 active
- [x] 永不日志/响应 api_key
- [x] 无 v6_* / 无新依赖 / 未 commit

### Concerns（非阻塞）

1. **试连用 GET /models**：与 studio 一致；部分仅支持 chat 的网关可能失败，属既有探测语义。
2. **映射 provider 可不 active**：按设计可覆盖；禁用/无 key 时在调用侧人话失败。
3. **日志写失败仅打 exception**：不阻断试连结果。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 |
|--------|------|
| SYNC test_model_provider | ✅ `SYNC_PROVIDER_TEST_COMMANDS` + `provider_test` + dispatcher 同步路由 |
| mock HTTP / sqlite_test | ✅ `@patch(requests.get)`；23/23 复验通过 |
| CONNECTIVITY_TEST | ✅ 成功/失败均写；日志无 api_key |
| mapping overrides active | ✅ `resolve_for_role` + `executor` 按 `recipe.role` 传 `config` |
| REST …/test/ | ✅ 复用 `test_provider_connectivity` |
| 测试 | ✅ 8 case + orch/projects 回归 |
| 约束 | ✅ 无 v6_* / 无新依赖 / 未 commit |

**Notes（非阻塞）：** 缺「供应商不存在 / 缺配置 / 网络异常」单测；`resolve_for_role` 对映射 provider 固定 `enabled=True`（与 self-review 一致，可接受）。

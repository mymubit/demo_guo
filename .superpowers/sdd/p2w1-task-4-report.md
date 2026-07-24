# P2-W1 Task 4 Report — executor 接入 router；试连不走链

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** `_default_llm_call` → `chat_with_failover`；`provider_test` 仍直连，不写 FailoverAttempt

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/orchestrator/llm_router.py` | Added `FailoverCallContext` + `failover_call_scope` / `get_failover_call_context` |
| `backend/apps/drama/skills_bridge/executor.py` | `execute_generation` set context；`_default_llm_call` 有 ctx 时走 router |
| `backend/apps/drama/orchestrator/provider_test.py` | Doc 明确禁止走 `chat_with_failover`（逻辑未改，仍 GET `/models`） |
| `backend/apps/drama/tests/test_v3_failover_executor.py` | Created — failover + 试连 attempt=0 |
| `backend/apps/drama/tests/test_v3_provider_test.py` | 成功试连断言 `V3FailoverAttempt.count()==0` |

---

## TDD Evidence

### Step 1 — RED（实现前）

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_provider_test --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL（errors=1）

```
ERROR: test_execute_generation_failovers_and_writes_attempts
GenerationError: LLM HTTP 503: unavailable
```

原因：`_default_llm_call` 仍单跳 `LlmProvider.chat_completion`，首跳 503 直接失败，无 backup、无 `V3FailoverAttempt`。  
试连相关断言已绿（本就未走链）。

### Step 2 — Implementation

1. **contextvars** — `failover_call_scope(owner, run, project)` 在 `execute_generation` 包裹 LLM 调用。
2. **`_default_llm_call`** — 有 ctx → `chat_with_failover`；无 ctx → 旧单跳（保留 `llm_call=` 注入绕过与直接调 `_default_llm_call` 单测）。
3. **空链友好提示** — `已尝试供应商：(无)` 映射为「请先在模型配置中配置并启用供应商」。
4. **试连** — 不调用 router；断言 attempt 数为 0。

### Step 3 — GREEN

同 RED 命令 + smoke：

```powershell
py -3 manage.py test apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_provider_test apps.drama.tests.test_v3_skills_bridge.ExecuteGenerationTests apps.drama.tests.test_v3_llm_router --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — `Ran 20 tests in 6.379s`

| Test | Covers |
|------|--------|
| `test_execute_generation_failovers_and_writes_attempts` | 503→backup；≥2 attempts；`project_brief` candidate |
| `test_connectivity_does_not_create_failover_attempts` | 试连 `count()==0` |
| provider_test 成功路径断言 | 同上 |
| `ExecuteGenerationTests`（含 `llm_call=`） | 注入绕过 router 仍绿 |
| `test_v3_llm_router` | 路由单测未回归 |

---

## Self-Review

| Check | Result |
|-------|--------|
| `_default_llm_call` 经 `chat_with_failover` | ✓（有 FailoverCallContext 时） |
| owner/run/project 经 contextvars | ✓ |
| 注入 `llm_call=` 绕过 router | ✓ |
| `provider_test` / `test_model_provider` 不走链 | ✓ |
| 无 Usage/ECharts/prices | ✓ |
| 未 git commit | ✓ |

**Concerns:** `chat_with_failover` 跳过空 `provider_id` hop，纯 env 配置链路仍无法经 router 调用（与 Task 3 行为一致）；无 ctx 时仍单跳，仅 `execute_generation` 默认路径写 attempt。

---

## Commit

Skipped per task brief.

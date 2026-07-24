# P2-W1 Task 3 Report — llm_router 按链调用并写 FailoverAttempt

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** `orchestrator/llm_router.py` + unit tests only (no executor wiring)

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/orchestrator/llm_router.py` | Created — `chat_with_failover` |
| `backend/apps/drama/tests/test_v3_llm_router.py` | Created — 4 tests (brief 3 + call-log FK 绑定) |

---

## TDD Evidence

### Step 1 — RED (before implementation)

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_llm_router --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL

```
ModuleNotFoundError: No module named 'apps.drama.orchestrator.llm_router'
FAILED (errors=1)
```

### Step 2 — Implementation

1. **`chat_with_failover`** — `resolve_chain(role_key)` 遍历 hops；可注入 `chat_fn`，默认 `LlmProvider.chat_completion`；每次调用传 `config=hop.config`。
2. **Attempt 审计** — 成功写 `succeeded`（弱绑定同 `v3_command_run` 最新 `DramaLlmCallLog`）；可切换失败写 `failed_switchable` 后继续；不可切换写 `failed_terminal` 并原样 re-raise。
3. **链耗尽** — `LlmProviderError`，message 含「已尝试供应商：」+ 名称（顿号拼接）。
4. **空 / 缺失 provider_id** — 跳过该 hop（无法写必填 FK），不计入成功路径。

### Step 3 — GREEN (after implementation)

Same command as RED.

**Result:** OK

```
Creating test database for alias 'default'...
....
----------------------------------------------------------------------
Ran 4 tests in 1.473s

OK
```

| Test | Covers |
|------|--------|
| `test_failover_to_backup_on_switchable_error` | 503 → backup；2 attempts `failed_switchable` + `succeeded` |
| `test_exhausted_chain_raises_with_zh_summary` | 两跳均失败；中文「已尝试供应商」+ 名称 |
| `test_terminal_error_stops_without_backup` | `empty_response` 不进第二跳；`failed_terminal` |
| `test_success_binds_latest_call_log_for_run` | 成功 attempt 挂最新同 run call log |

---

## Self-Review

| Check | Result |
|-------|--------|
| Interface matches brief (`chat_with_failover` kwargs / return) | ✓ |
| Uses `failover_policy.resolve_chain` + `classify_provider_error` | ✓ |
| Writes `V3FailoverAttempt` per hop | ✓ |
| Mock `chat_fn` — no real network | ✓ |
| No executor / provider_test wiring (Task 4) | ✓ |

**Concerns:** 空 `provider_id` hop 被静默跳过；若整链皆空，耗尽文案为「已尝试供应商：(无)」。失败 attempt 不绑 call log（brief 仅要求成功路径弱关联）。executor 接入留给 Task 4。

---

## Commit

Skipped per project rule (user did not request commit).

---

## P2-W1 Final Important Fix (2026-07-23)

**Issue:** `chat_with_failover` 对 `provider_id==""` 的 env-only hop 直接 `continue`，无 DB provider 时生成链路无法调用 LLM。

**Fix:**
1. 空 `provider_id` 仍调用 `invoke(..., config=hop.config)`，成功直接返回。
2. `tried_names` 使用 `hop.provider_name` 或 `"环境配置"`。
3. env-only 路径不写 `V3FailoverAttempt`（无 FK provider）。
4. `provider_id` 非空但 DB 行缺失 — 保持跳过。

**Test:** `test_env_only_hop_succeeds_without_failover_attempt` — patch `resolve_chain` 返回空 provider_id hop；mock `chat_fn` 成功；断言 response 返回且 `FailoverAttempt.count()==0`。

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_llm_router --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — Ran 5 tests in 1.843s

**Files changed:** `backend/apps/drama/orchestrator/llm_router.py`, `backend/apps/drama/tests/test_v3_llm_router.py`, `.superpowers/sdd/p2w1-task-3-report.md`

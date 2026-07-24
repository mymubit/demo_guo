# P2-W1 Task 2 Report — failover_policy 链解析 + 错误可切换判定

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** `orchestrator/failover_policy.py` + unit tests only (no llm_router / executor wiring)

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/orchestrator/failover_policy.py` | Created — `ProviderHop`, `resolve_chain`, `classify_provider_error` |
| `backend/apps/drama/tests/test_v3_failover_policy.py` | Created — 15 tests (brief + Spec §5 coverage) |

---

## TDD Evidence

### Step 1 — RED (before implementation)

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_policy --settings=config.settings.sqlite_test -v 1
```

**Result:** FAIL

```
ModuleNotFoundError: No module named 'apps.drama.orchestrator.failover_policy'
FAILED (errors=1)
```

### Step 2 — Implementation

1. **`ProviderHop`** — frozen dataclass with `provider_id`, `provider_name`, `config: ResolvedLlmConfig`, `attempt_index`.
2. **`resolve_chain(role_key)`**
   - 有 `V3RoleModelMapping`：主 `provider` + `backup_provider_ids` 去重保序；跳过不存在 UUID；每跳用 `_config_from_provider` 复用 `decrypt_secret` / 映射级 `temperature`/`max_tokens`。
   - 无映射 / 空 role：单跳，等价 `LlmConfigService.resolve()` + active provider 元数据。
3. **`classify_provider_error(exc)`** — Spec §5：
   - 可切换：`TimeoutError` / `requests.exceptions.Timeout`、连接类、`LlmProviderError` 禁用/配置不全文案、`LLM HTTP 401/403/408/429/5xx`（消息前缀对齐 `llm_provider.py`）。
   - 不可切换：其它 HTTP（如 400）、`LLM 流式响应为空`、通用异常（`unknown`, False）。

### Step 3 — GREEN (after implementation)

Same command as RED.

**Result:** OK

```
Creating test database for alias 'default'...
...............
----------------------------------------------------------------------
Ran 15 tests in 0.009s

OK
```

---

## Self-Review

| Check | Result |
|-------|--------|
| Interfaces match brief (`ProviderHop`, `resolve_chain`, `classify_provider_error`) | ✓ |
| Reuses `ResolvedLlmConfig` / `LlmConfigService` patterns (no duplicate config type) | ✓ |
| HTTP / 禁用 / 配置文案与 `llm_provider.py` 对齐 | ✓ |
| Dedup + skip missing backup ids | ✓ |
| Mapping temperature/max_tokens apply to whole chain | ✓ |
| No llm_router / executor scope creep | ✓ |

**Concerns:** `resolve_chain` 无映射时若 DB 无 active provider 仍返回单跳（`provider_id=""`，config 来自 env/none）；与今日 `resolve_for_role` 回退一致，router 层需处理空 id。Backup 启用校验仍留给 Models write API（Task 1 已注明）。

---

## Commit

Skipped per project rule (user did not request commit).

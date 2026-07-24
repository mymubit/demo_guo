# P2-W1 Task 6 Report — Logs API + LogsPage 展示 failover_attempts

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** GET `/api/v3/logs/runs/{id}/` 增加 `failover_attempts`；LogsPage 详情抽屉「切换尝试」；OpenAPI + TS；无 commit

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/api/v3/logs_views.py` | run detail 序列化 `failover_attempts`（按 `attempt_index`） |
| `backend/apps/drama/tests/test_v3_logs_api.py` | +`test_run_detail_includes_failover_attempts` |
| `docs/contracts/v3/openapi.yaml` | `FailoverAttempt` schema；`LogRun.failover_attempts` |
| `frontend/src/types/v3/domain.ts` | `FailoverAttempt` / `FailoverAttemptStatus`；`LogRun.failover_attempts` |
| `frontend/src/pages/LogsPage.tsx` | 详情抽屉「切换尝试」中文状态文案 |
| `frontend/src/pages/LogsPage.test.tsx` | mock attempts 时可见「切换尝试」/供应商名 |
| `frontend/src/types/v3/api.test.ts` | 契约冒烟含 `FailoverAttempt` / `failover_attempts` |

---

## TDD Evidence

### Step 1 — RED

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_logs_api.V3LogsApiTests.test_run_detail_includes_failover_attempts --settings=config.settings.sqlite_test -v 2
```

**Result:** FAIL — `'failover_attempts' not found in {...}`

```powershell
cd c:\Users\99193\Desktop\demo_guo\frontend
npm test -- --run src/pages/LogsPage.test.tsx
```

**Result:** FAIL — `Unable to find an element with the text: 切换尝试`

### Step 2 — Implementation

- Detail：`V3FailoverAttempt` → `{id, attempt_index, provider_id, provider_name, status, error_code, error_message, llm_call_log_id, created_at}`
- UI：有 attempts 时渲染「切换尝试」；状态映射 `succeeded/failed_switchable/failed_terminal/skipped` → 中文
- 空数组时不展示该区块；仍不渲染 operation/recipe

### Step 3 — GREEN

```powershell
# Backend
py -3 manage.py test apps.drama.tests.test_v3_logs_api --settings=config.settings.sqlite_test -v 1
# OK — Ran 7 tests

# Frontend
npm test -- --run src/pages/LogsPage.test.tsx
# OK — 8 passed
```

---

## Self-Review

| Check | Result |
|-------|--------|
| API 形状与 brief 一致 | ✓ |
| 按 attempt_index 升序 | ✓ |
| UI「切换尝试」+ 供应商名 + 中文状态 | ✓ |
| 无 operation/recipe 渲染 | ✓ |
| OpenAPI + TS 同步 | ✓ |
| 未 git commit | ✓ |

**Concerns:** Spec §7 提及「耗时」字段，当前 API/模型无 per-attempt latency，UI 仅展示 `created_at`；空 attempts 时区块隐藏（与「有则展示」一致）。

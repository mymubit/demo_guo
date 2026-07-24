# P2-W2 Task 2 Report — V3UsageDailyRollup + increment helper

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** Model + migration `0022` + `orchestrator/usage_rollup.py` + sync wire in `LlmCallLogService.record`

---

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/models.py` | Modified — new `V3UsageDailyRollup` (§4.4 + `unpriced_call_count`) |
| `backend/apps/drama/migrations/0022_v3_usage_daily_rollup.py` | Created via `makemigrations` |
| `backend/apps/drama/orchestrator/usage_rollup.py` | Created — `shanghai_date` / `estimate_cost` / `apply_call_to_rollup` |
| `backend/apps/drama/services/llm_call_log_service.py` | Modified — after create, sync `apply_call_to_rollup` |
| `backend/apps/drama/tests/test_v3_usage_rollup.py` | Created — TDD |

---

## TDD Evidence

### RED

```
ImportError: cannot import name 'V3UsageDailyRollup' from 'apps.drama.models'
FAILED (errors=1)
```

### GREEN

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_rollup --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — `Ran 7 tests` (priced cost / unpriced count / same-day upsert / service wire / shanghai_date / estimate_cost)

---

## Behavior Notes

- `date` = Asia/Shanghai calendar day
- Provider：`base_url` (+ `model_name`) 反查 `DramaLlmProvider`；无 `V3ModelPrice` → `unpriced_call_count += 1`，不累加 `estimated_cost`
- Owner：`v3_command_run.owner` → `v3_project.owner`；皆无则 skip
- SQLite 对 `nulls_distinct=False` 有 W047（约束不建）；应用层 upsert 仍正确；PostgreSQL 生产约束生效

## Commit

Skipped per brief.

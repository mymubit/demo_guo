# P2-W2 Task 4 Report — Usage summary API

**Status:** DONE  
**Date:** 2026-07-23

## Deliverables

| File | Action |
|------|--------|
| `backend/apps/drama/tests/test_v3_usage_api.py` | Created — 11 TDD cases |
| `backend/apps/drama/api/v3/usage_views.py` | Created — `V3UsageSummaryView` |
| `backend/apps/drama/api/v3/urls.py` | Modified — `usage/summary/` |
| `docs/contracts/v3/openapi.yaml` | Modified — path + schemas |
| `frontend/src/types/v3/domain.ts` | Modified — `UsageSummary*` types |
| `frontend/src/types/v3/api.ts` | Modified — exports |
| `frontend/src/types/v3/api.test.ts` | Modified — contract checks |
| `frontend/src/services/v3/usage.ts` | Created — `getUsageSummary` |

## TDD Evidence

**RED:** 10× `404 Not Found` on `/api/v3/usage/summary/`（+1 patch 目标缺失）

**GREEN:**
```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_api --settings=config.settings.sqlite_test -v 1
# Ran 11 tests — OK
```

Frontend: `npm test -- src/types/v3/api.test.ts --run` — 8 passed

## Contract

- **GET** `/api/v3/usage/summary/?project_id=&date_from=&date_to=&group_by=day|model|command_type&live=0|1`
- `timezone` 固定 `Asia/Shanghai`；`rows`/`totals` 含 `unpriced_call_count`
- 默认读 `V3UsageDailyRollup`（owner 隔离）；`live=1` 合并近 6 小时 `DramaLlmCallLog`

## Commit

Skipped per instruction.

---

## Important Fix — live=1 重复计数（2026-07-23）

**问题：** 同步 rollup 已含近窗 call；原 `live=1` 再 merge 近 6h log → 双计。  
**修复：** `live=1` 仅从 `DramaLlmCallLog` 按 Shanghai `[date_from, date_to]` 聚合，跳过 rollup。  
**测试：** `test_live_aggregates_call_logs_in_date_range`、`test_live_no_double_count_when_rollup_has_same_call`；12/12 OK。  
**详情：** `.superpowers/sdd/p2w2-task-4-live-fix.md`

# P2-W2 Task 4 — live=1 重复计数修复

**Date:** 2026-07-23  
**Severity:** Important

## 根因

Task 2 在 call log 落库后同步 `apply_call_to_rollup`；Task 4 原 `live=1` 将近 6h call log **叠加**到 rollup，同窗数据被计两次。

## 修复

`live=1` 时**忽略 rollup**，仅按 `[date_from, date_to]`（Asia/Shanghai 日界）聚合 `DramaLlmCallLog`，仍支持 owner / `project_id` / `group_by`。

## 变更

| File | Change |
|------|--------|
| `backend/apps/drama/api/v3/usage_views.py` | live 分支改为 call-log-only；移除 6h cutoff 与 `_merge_buckets` |
| `backend/apps/drama/tests/test_v3_usage_api.py` | 重写 live 用例；新增 `test_live_no_double_count_when_rollup_has_same_call` |

## 验证

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_api --settings=config.settings.sqlite_test
# Ran 12 tests — OK
```

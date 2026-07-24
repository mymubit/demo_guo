# W6 Task 6 报告：删旧守卫测 + CI 友好断言

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — 删旧守卫测  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-6-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 6

---

## What I Implemented

新建 `backend/apps/drama/tests/test_v3_legacy_gone.py`，三类守卫：

### 1. Filesystem

- 后端已删路径 `assertFalse(exists)`：`v2_{urls,views,serializers,service}.py`、`services/v6_{runtime,workbench,control_plane}.py`、`services/generation_service.py`
- 前端：`frontend/src/studio` 目录不存在

### 2. Route

- `GET /api/v2/studio/bootstrap/` → HTTP 410，信封 `code=410`，message 含 `/api/v3`

### 3. Source scan

扫描根：`orchestrator/`、`skills_bridge/`、`api/v3/`、`tasks_v3.py`  
Banned：`v6_runtime` | `v6_workbench` | `v6_control_plane` | `/api/v2/studio`

### 4. 前端 router（保留既有）

未改 `frontend/src/app/router.test.tsx`：仍断言 `V3_NAV_PATHS` 无 `/studio*`，且含 `/billing`。

---

## Verification

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_legacy_gone --settings=config.settings.sqlite_test -v 2
```

| 命令 | 结果 |
|------|------|
| `test_v3_legacy_gone` | **4 passed**，exit 0 |

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/tests/test_v3_legacy_gone.py` | 新建 |
| `.superpowers/sdd/w6-task-6-report.md` | 本报告 |

---

## Concerns

1. 与 `test_v2_gone.py`、`test_v3_async_commands.test_no_v6_runtime_*` 有部分重叠；本文件为 W6 §8.8 CI 聚合守卫，刻意保留。
2. 源码扫描仅覆盖 V3 产品路径；`skills_loader.v6_workbench` 等属性名仍可能存在于其它模块（Task 5 residual，非本守卫范围）。
3. 未跑全量 `apps.drama.tests`（属 Task 7 基线）。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 必检项 | 结果 |
|--------|------|
| Filesystem（v2_* / v6_* / generation_service / frontend studio） | ✅ 8 路径 + studio 目录 `assertFalse(exists)` |
| Route `/api/v2/studio/bootstrap/` → 410 + `code=410` + `/api/v3` | ✅ `V2GoneView` |
| Source scan（orchestrator / skills_bridge / api/v3 / tasks_v3） | ✅ 4 banned tokens 零命中 |
| 前端 router 无 studio（保留既有） | ✅ `router.test.tsx` 未改，含 `/billing` |

**Independent checks (2026-07-23):** `test_v3_legacy_gone` **4/4 OK**（`sqlite_test`，exit 0）；磁盘 `v2_urls.py` / `frontend/src/studio` 均不存在。

**非阻塞：** 与 `test_v2_gone` / `test_v3_async_commands.test_no_v6_runtime_*` 有重叠，符合 W6 §8.8 CI 聚合守卫意图；源码扫描不含 frontend（brief 未要求，Task 7 rg 覆盖）。

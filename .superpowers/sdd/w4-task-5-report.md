# W4 Task 5 报告：Quality REST API

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — Quality REST API  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. `api/v3/quality_views.py`（新建）

对齐 `episodes_views` / `scripts_views`：owner 隔离 + `dispatch_command`。

| Method | Path | 行为 |
|--------|------|------|
| GET | `quality/` | QualityState：双报告、findings、stale、latest runs |
| POST | `quality/score/` | → `score_quality` |
| POST | `quality/compliance/` | → `check_compliance` |
| POST | `quality/accept/` | → `accept_findings` |
| POST | `quality/revise/` | → `revise_from_findings` |

- `quality_is_stale` / `compliance_is_stale` 经 `report_meta.is_report_stale`（无报告时为 `false`）
- `latest_quality_run`：`score_quality` / `revise_from_findings` / `accept_findings`
- `latest_compliance_run`：`check_compliance`
- 信封 `{ code, message, data }`；失败 run 为人话 `error_message`，无 Traceback

### 2. `api/v3/serializers.py`

- `QualityFindingSerializer`（含 `report_artifact_id`）
- `QualityAcceptSerializer` / `QualityAcceptFindingItemSerializer`（`source` + `finding_key` 必填）
- `QualityReviseSerializer`（可选 `finding_keys`、`episode_range.start/end`）

### 3. `api/v3/urls.py`

挂载上述 5 条路由于 `/api/v3/projects/<uuid>/quality/…`。

### 4. `tests/test_v3_quality_api.py`

8 cases：空态、stale/findings、score+compliance、accept、accept 校验 400、revise 候选、episode_range 非法、owner 404。

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_quality_api --settings=config.settings.sqlite_test -v 2
```

**结果：** PASS — **8 tests, OK**

`rg v6_runtime|v6_workbench|v6_control_plane` 于 `quality_views.py`：无匹配。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/api/v3/quality_views.py` | 新建 |
| `backend/apps/drama/api/v3/serializers.py` | 扩展 |
| `backend/apps/drama/api/v3/urls.py` | 修改 |
| `backend/apps/drama/tests/test_v3_quality_api.py` | 新建 |

---

## Concerns

1. OpenAPI 路径段尚未为 `/quality/*` 写 path 条目（仅有 QualityState schema）；Task 7 前端可按本实现契约对接。
2. `latest_quality_run` 合并了 score/revise/accept；若前端需独立轮询 revise，可再拆字段。
3. GET 无报告时 `*_is_stale=false`（非「无效」）；过期横幅应在有报告且 stale 时展示。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 要求 | 结论 |
|------|------|
| GET `quality/`（双报告、findings、stale、latest runs） | ✅ 对齐 OpenAPI `QualityState` |
| POST score/compliance/accept/revise | ✅ 经 `dispatch_command` 接线四命令 |
| 信封 `{ code, message, data }` | ✅ `api_response` |
| owner 404 隔离 | ✅ `_owned_v3_project`；5 路由均测 |
| finding_key 对齐 gate/accept | ✅ `source`+`finding_key` 必填 → `accept_findings` |
| 人话错误、无 Traceback | ✅ 成功 run 断言；dispatcher 人话 `error_message` |
| episodes/scripts 模式 | ✅ 同 `_serialize_artifact` / `_latest_run` 结构 |
| Mock LLM / 无 v6_* / 无新依赖 | ✅ 8 tests OK；`quality_views.py` 无 v6 引用 |

**备注（非阻断）：** OpenAPI 仍缺 `/quality/*` path 条目（schema 已有，与 W4 Task 1 延期一致）；`latest_quality_run` 合并 score/revise/accept；缺 failed-run 人话错误单测。

**缺陷：** 无。

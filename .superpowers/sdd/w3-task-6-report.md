# W3 Task 6 Review — Scripts REST API + 草稿（只读）

**Date:** 2026-07-23  
**Scope:** `api/v3/scripts_views.py`、`serializers.py`、`urls.py`、`orchestrator/confirm.py`（use_drafts）、`openapi.yaml`、`test_v3_scripts_api.py`  
**Tests:** `test_v3_scripts_api` — 9/9 OK（本地复跑）

---

## Verdicts

| 维度 | 结论 |
|------|------|
| **Spec** | ✅ |
| **Quality** | Approved |

---

## 必查项

| 项 | 结论 | 依据 |
|----|------|------|
| **GET** `{ committed, candidate, drafts[], latest_run }` | ✅ | `V3ScriptsStateView` + `_scripts_state`；`episode_scripts` + `V3ScriptDraft` |
| **GET 单集** committed/candidate 切片 + draft | ✅ | `V3ScriptEpisodeView` + `_episode_slice` |
| **PUT draft** | ✅ | `V3ScriptDraftView` update_or_create；缺 payload → 400 |
| **POST generate** | ✅ | `dispatch_command(write_episode_batch)`；`start/end` → `episode_range`；缺参 → 400 |
| **POST confirm** | ✅ | `dispatch_command(confirm_script_candidate)`；默认确认 AI candidate |
| **use_drafts + schema validate** | ✅ | `_merge_script_drafts` → `validate_artifact_payload("episode_scripts", …)` → 新 committed；测例断言 validate 通过且 script 含草稿内容 |
| **Owner 隔离** | ✅ | 五端点均 `_owned_v3_project` → 非 owner 404；generate/confirm 另经 `_resolve_project(owner=…)` |
| **OpenAPI** | ✅ | 5 paths + `ScriptsState` / `ScriptEpisodeState` / `ScriptDraft*` / `ScriptConfirmRequest` |

---

## 测例摘要

| # | 用例 | 结果 |
|---|------|------|
| 1 | GET 空状态 | PASS |
| 2 | PUT draft → 列表含草稿；覆盖更新 | PASS |
| 3 | GET 单集切片 | PASS |
| 4 | generate → candidate → confirm → committed | PASS |
| 5 | `use_drafts=true` 合并 + validate + committed | PASS |
| 6 | `use_drafts` 无草稿 → failed 人话 | PASS |
| 7 | generate 缺 start/end → 400 | PASS |
| 8 | PUT draft 缺 payload → 400 | PASS |
| 9 | Owner 隔离五端点 404 | PASS |

---

## 备注（非阻塞）

1. PUT draft 不校验 schema（与 Topic 一致）；校验仅在 confirm `use_drafts` 路径——符合 brief。
2. `use_drafts` 需已有 committed/candidate 底稿；纯草稿或集号不在底稿中会 failed——行为合理，已在实现报告说明。
3. 缺 `use_drafts` 校验失败负例测（非法 scenes 结构）——可后续补，不挡本任务。

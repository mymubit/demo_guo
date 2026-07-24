# W3 Task 5 Review — Episodes REST API（只读）

**Date:** 2026-07-23  
**Scope:** `api/v3/episodes_views.py`、`serializers.py`、`urls.py`、`openapi.yaml`、`test_v3_episodes_api.py`  
**Tests:** `test_v3_episodes_api` — 6/6 OK（本地复跑）

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
| **GET** `{ stage, committed, candidate, latest_run }` | ✅ | `V3EpisodesStateView` + `_episodes_state`；单产物 `episode_plan` |
| **POST generate** | ✅ | `dispatch_command(generate_episode_plan)`；透传 `episode_count` / `duration_target` / `planning_requests` |
| **POST confirm** | ✅ | `dispatch_command(confirm_episode_plan)` |
| **POST revise** | ✅ | `dispatch_command(revise_episode_plan)`；必填 `episode_numbers` |
| **Owner 隔离** | ✅ | 四端点均 `_owned_v3_project` → 非 owner 404；测例覆盖 |
| **OpenAPI** | ✅ | 4 paths + `EpisodesState` / `EpisodeGenerateRequest` / `EpisodeReviseRequest` / `EnvelopeEpisodesState`；与实现一致 |

---

## 测例摘要

| # | 用例 | 结果 |
|---|------|------|
| 1 | GET 空状态 | PASS |
| 2 | generate → candidate → confirm → committed + `stage=writing` | PASS |
| 3 | revise 指定集 → 新 candidate，未改集不变 | PASS |
| 4 | revise 缺 `episode_numbers` → 400 | PASS |
| 5 | 无蓝图 generate → failed 人话 | PASS |
| 6 | Owner 隔离四端点 404 | PASS |

---

## 备注（非阻塞）

1. `episode_count` 等参数 API 层仅透传；executor/skills 是否消费属后续接线（brief 已说明）。
2. Episodes GET 含 `stage`，Blueprint GET 不含——与 Topic 对齐，前端需注意差异。

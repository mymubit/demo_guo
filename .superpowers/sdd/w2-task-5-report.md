# W2 Task 5 报告：Topic / Blueprint REST API

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W2 — 选题/蓝图 REST API（generate / draft / confirm）

---

## What I Implemented

### 1. Topic API（`api/v3/topic_views.py`）

| 方法 | 路径 | 行为 |
|------|------|------|
| GET | `/api/v3/projects/{id}/topic/` | `{ stage, committed, candidate, draft, latest_run }` |
| PUT | `/api/v3/projects/{id}/topic/draft/` | upsert `project_brief` draft |
| POST | `/api/v3/projects/{id}/topic/generate/` | `dispatch_command(generate_topic_brief)` |
| POST | `/api/v3/projects/{id}/topic/confirm/` | `dispatch_command(confirm_topic_brief)`，支持 `use_draft` |

### 2. Blueprint API（`api/v3/blueprint_views.py`）

| 方法 | 路径 | 行为 |
|------|------|------|
| GET | `/api/v3/projects/{id}/blueprint/` | `{ committed, candidate, latest_run }`（五 key 聚合） |
| POST | `.../blueprint/generate/` | `dispatch_command(generate_blueprint)` |
| POST | `.../blueprint/confirm/` | `dispatch_command(confirm_blueprint)` |

### 3. Confirm `use_draft`

- `orchestrator/confirm.py`：`confirm_topic_brief` 在 `use_draft=true` 时将 draft 升为 committed，并 supersede 旧 committed/candidate；推进 `stage` topic→blueprint

### 4. Serializers / URLs / OpenAPI

- `ArtifactVersionSerializer`、`TopicDraftPutSerializer`、`TopicConfirmSerializer`、`BlueprintConfirmSerializer`
- `urls.py` 挂载 topic/blueprint 路由
- `docs/contracts/v3/openapi.yaml` 补充路径与 schema

### 5. 回归修正

- `test_v3_projects_crud`：原 `generate_topic_brief` unsupported 断言改为仍 stub 的 `generate_episode_plan`

---

## TDD: RED → GREEN

### Step 1: RED

**命令：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL（7）— 路由 404（未实现）

### Step 2: 实现

- topic_views / blueprint_views / serializers / urls
- confirm `use_draft`
- openapi.yaml
- W1 CRUD stub 命令断言更新

### Step 3: GREEN

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api -v 1 --settings=config.settings.sqlite_test
```

**结果：** PASS — 47 tests, OK (~36.6s)

**grep：** `api/v3` / orchestrator / skills_bridge / tasks_v3 无 `v6_runtime|v6_workbench|v6_control_plane`

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/api/v3/topic_views.py` | 新建 |
| `backend/apps/drama/api/v3/blueprint_views.py` | 新建 |
| `backend/apps/drama/api/v3/serializers.py` | 修改 |
| `backend/apps/drama/api/v3/urls.py` | 修改 |
| `backend/apps/drama/orchestrator/confirm.py` | 修改（use_draft） |
| `docs/contracts/v3/openapi.yaml` | 修改 |
| `backend/apps/drama/tests/test_v3_topic_api.py` | 新建 |
| `backend/apps/drama/tests/test_v3_blueprint_api.py` | 新建 |
| `backend/apps/drama/tests/test_v3_projects_crud.py` | 修改 |
| `.superpowers/sdd/w2-task-5-report.md` | 本报告 |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD（先测后实现，见 RED 404） | ✓ |
| eager + `V3_LLM_CALL_OVERRIDE` mock | ✓ |
| generate→candidate→confirm→committed 主链 | ✓ |
| owner 隔离 404 | ✓ |
| OpenAPI 已更新 | ✓ |
| W1 CRUD 回归绿 | ✓ |
| 无 v6_runtime 引用 | ✓ |

---

## Concerns / Follow-ups

- **蓝图无 draft API**：W2 仅选题提供 `PUT .../topic/draft/`；蓝图 confirm 的 `use_draft` 字段预留但未实现草稿路径。
- **draft 不做 schema 校验**：保存草稿允许任意 object；确认时也不走 `validate_artifact_payload`（与 candidate 确认路径一致，均信任已有 payload）。
- **非 eager 响应**：generate 在生产返回 `queued`；前端需轮询 `latest_run`（Task 6/7）。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `test_v3_topic_api` | 5 | PASS |
| `test_v3_blueprint_api` | 4 | PASS |
| `test_v3_projects_crud` | 6 | PASS |
| W1/W2 相关合计（含 artifact/skills/async/orchestrator/contract/domain） | 47 | PASS |

# W1 Task 3 报告：`/api/v3` 项目 CRUD + commands 端点

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 项目 CRUD + commands HTTP 端点  
**Commits:** none

---

## What I Implemented

### 1. Serializers（`api/v3/serializers.py`）

- 保留 `CreateProjectSerializer` / `ProjectSummarySerializer`
- 新增 `DispatchCommandSerializer`：`command_type`、`payload`、`idempotency_key?`
- 新增 `CommandRunSerializer`：`id, command_type, status, project_id, error_message, result_payload, created_at, updated_at`

### 2. Views（`api/v3/views.py`）

- `GET /projects/`：默认 `archived_at ISNULL`；`include_archived=1|true` 含归档
- `POST /projects/`：内部 `dispatch_command(create_project)`，成功仍返回 `ProjectSummary`（W0 兼容）
- `POST /projects/{id}/archive/`：设 `archived_at=now()`，幂等；非本人 404
- `POST /commands/`：→ `{command_run, project?}`
- `GET /commands/{run_id}/`：本人运行详情

### 3. URLs（`api/v3/urls.py`）

- 追加 `archive/`、`commands/`、`commands/<run_id>/`

### 4. OpenAPI（`docs/contracts/v3/openapi.yaml`）

- 追加 `include_archived` query、`/projects/{id}/archive/`、`/commands/`、`/commands/{run_id}/`
- 新增 `CommandRun`、`DispatchCommandRequest`、`CommandDispatchResult` 等 schema

### 5. 测试 `test_v3_projects_crud.py`

六用例（APITestCase + force_authenticate）：

1. create via POST `/projects/` → 200 + stage topic  
2. list 默认排除 archived  
3. archive 后 list 空；`include_archived=1` 可见；再 archive 幂等  
4. POST `/commands/` create_project → succeeded + project  
5. POST `/commands/` generate_topic_brief → unsupported  
6. 他用户 project archive → 404  

---

## TDD: RED → GREEN

### Step 1–2: RED（失败测试）

**命令：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_projects_crud -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL（4 failures / 2 ok）

| 用例 | 结果 | 原因 |
|------|------|------|
| create via POST | ok | W0 已有端点 |
| list excludes archived | FAIL | 列表未过滤 `archived_at` |
| archive + include_archived | FAIL | 无 `/archive/` 路由 → 404 |
| commands create_project | FAIL | 无 `/commands/` 路由 → 404 |
| commands generate_topic_brief | FAIL | 无 `/commands/` 路由 → 404 |
| 他用户 archive 404 | ok | 路由缺失亦返回 404（假阳性，实现后仍为所有权 404） |

### Step 3: 实现

- 修改 `serializers.py` / `views.py` / `urls.py`
- 更新 `docs/contracts/v3/openapi.yaml`

### Step 4: GREEN + 回归

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS

```
Ran 14 tests in 11.235s
OK
```

- W0 smoke：3 ok  
- projects CRUD：6 ok  
- orchestrator：3 ok  
- domain w1：2 ok  

---

## Concerns

1. `POST /projects/` 失败路径返回 `{command_run}` + HTTP 400（校验失败仍走 DRF 400）；W0 仅覆盖成功路径。  
2. `ProjectSummary` 尚未暴露 `archived_at`（Task 4 前端类型可能需要补字段）。  
3. RED 阶段「他用户 404」因路由缺失假通过；GREEN 后由 `_owned_v3_project` 真正保证所有权。  
4. `GET /commands/{run_id}/` 无独立用例（brief 六用例未列）；实现已就绪。  

---

## Files Touched

- `backend/apps/drama/api/v3/serializers.py`
- `backend/apps/drama/api/v3/views.py`
- `backend/apps/drama/api/v3/urls.py`
- `backend/apps/drama/tests/test_v3_projects_crud.py`（new）
- `docs/contracts/v3/openapi.yaml`
- `.superpowers/sdd/w1-task-3-report.md`（本文件）

---

## Review Fix: ProjectSummary.archived_at（2026-07-23）

**Finding:** W1 Task 3 review — `ProjectSummary` 必须包含可空字段 `archived_at`。

### Changes

1. **`backend/apps/drama/api/v3/serializers.py`** — `ProjectSummarySerializer.Meta.fields` 追加 `archived_at`。
2. **`docs/contracts/v3/openapi.yaml`** — `ProjectSummary` schema 追加 `archived_at: { type: string, format: date-time, nullable: true }`。
3. **`backend/apps/drama/tests/test_v3_projects_crud.py`** — `test_archive_hides_from_list_unless_include_archived` 断言：
   - archive 响应 `data.archived_at` 非空；
   - `include_archived=1` 列表项 `archived_at` 非空。

### Verification

**命令：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_contract_smoke -v 1 --settings=config.settings.sqlite_test
```

**结果：** PASS

```
Ran 9 tests in 8.231s
OK
```

**Commits:** none

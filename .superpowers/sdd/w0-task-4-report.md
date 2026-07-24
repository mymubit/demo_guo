# W0 Task 4 报告：后端 `/api/v3` 空壳 + 契约冒烟测试

**Status:** DONE  
**Date:** 2026-07-22  
**Task:** ScriptForge V3 W0 — 后端 `/api/v3` 空壳 + 契约冒烟测试  
**Commits:** none（按指令未提交）

---

## Note on Brief

`.superpowers/sdd/w0-task-4-brief.md` 当时不存在；按  
`docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md` Task 4 与用户下发的 Interfaces 执行。

---

## What I Implemented

### 1. TDD 流程（严格 RED → GREEN）

| 阶段 | 命令 | 结果 |
|------|------|------|
| RED | `py -3 manage.py test apps.drama.tests.test_v3_contract_smoke -v 2 --settings=config.settings.sqlite_test` | **FAIL** — 3 failures，`/api/v3/*` 均为 404 |
| GREEN | 同上（实现模型/路由/视图后） | **PASS** — 3 tests ok |

### 2. RED 证据

```
Found 3 test(s).
...
WARNING ... Not Found: /api/v3/billing/plans/
FAIL
WARNING ... Not Found: /api/v3/projects/
FAIL
WARNING ... Not Found: /api/v3/projects/
FAIL

======================================================================
FAIL: test_billing_plans_readonly_shell ...
AssertionError: 404 != 200
======================================================================
FAIL: test_create_project_returns_summary ...
AssertionError: 404 != 200
======================================================================
FAIL: test_list_projects_envelope ...
AssertionError: 404 != 200

Ran 3 tests in 1.104s
FAILED (failures=3)
```

### 3. GREEN 证据

```
Found 3 test(s).
...
Applying drama.0012_v3_project... OK
test_billing_plans_readonly_shell ... ok
test_create_project_returns_summary ... ok
test_list_projects_envelope ... ok

Ran 3 tests in 1.111s
OK
```

### 4. 新建 / 修改文件

| 路径 | 操作 | 内容 |
|------|------|------|
| `backend/apps/drama/tests/test_v3_contract_smoke.py` | 新建 | 列表信封 / 创建 summary / billing ≥3 + `price_label` |
| `backend/apps/drama/api/__init__.py` | 新建 | 包标记 |
| `backend/apps/drama/api/v3/__init__.py` | 新建 | 包标记 |
| `backend/apps/drama/api/v3/serializers.py` | 新建 | `CreateProjectSerializer`、`ProjectSummarySerializer` |
| `backend/apps/drama/api/v3/views.py` | 新建 | list/create/detail + 静态三档套餐 |
| `backend/apps/drama/api/v3/urls.py` | 新建 | `projects/`、`projects/<uuid>/`、`billing/plans/` |
| `backend/apps/drama/models.py` | 修改 | 追加 `V3Project` |
| `backend/apps/drama/migrations/0012_v3_project.py` | 新建 | CreateModel `V3Project`（另含无关 index rename，见 Concerns） |
| `backend/config/urls.py` | 修改 | **新增** `path("api/v3/", ...)`；**保留** `api/v2/studio/` |

---

## Contract Alignment

| 检查项 | 预期 | 实际 | 结果 |
|--------|------|------|------|
| 信封 | `{code, message, data}` via `api_response` | `code:0`，`message` 默认 `ok` | ✓ |
| `GET /api/v3/projects/` | `data.items` 为 list | 空列表信封 | ✓ |
| `POST /api/v3/projects/` | title / entry_type∈{original,adapt}；stage=`topic`；HTTP 200 | 与 OpenAPI/测试一致 | ✓ |
| `GET /api/v3/billing/plans/` | ≥3 档且含 `price_label` | 免费/专业/团队（对齐设计稿 §09） | ✓ |
| Auth | `IsAuthenticated`；测试 `force_authenticate` | 视图均挂 `IsAuthenticated` | ✓ |
| v2 保留 | 不删 `api/v2/studio/` | `config/urls.py` 仍 include | ✓ |

---

## Test Command Used

本机 `python` 不可用（Windows Store 别名），改用 `py -3`。  
按 `backend/README.md` 使用自包含 SQLite 设置：

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke -v 2 --settings=config.settings.sqlite_test
```

---

## Concerns

1. **Brief 缺失**：`w0-task-4-brief.md` 未落盘，执行依据为 W0 plan Task 4。
2. **迁移附带 RenameIndex**：`0012_v3_project.py` 顺带重命名 `DramaScriptDraft` 索引名（Django 状态漂移同步），与 V3 无关；后续若要纯净可拆 migration。
3. **创建 HTTP 状态**：V3 契约/测试要求 **200**（非 v2 的 201）。
4. **双项目表**：`V3Project` 与既有 `DramaProject` 并存，W0 刻意解耦；后续里程碑需明确是否桥接或迁移数据。

---

## Files Changed（汇总）

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/tests/test_v3_contract_smoke.py` | 新建 |
| `backend/apps/drama/api/__init__.py` | 新建 |
| `backend/apps/drama/api/v3/__init__.py` | 新建 |
| `backend/apps/drama/api/v3/serializers.py` | 新建 |
| `backend/apps/drama/api/v3/views.py` | 新建 |
| `backend/apps/drama/api/v3/urls.py` | 新建 |
| `backend/apps/drama/models.py` | 修改 |
| `backend/apps/drama/migrations/0012_v3_project.py` | 新建 |
| `backend/config/urls.py` | 修改 |
| `.superpowers/sdd/w0-task-4-report.md` | 新建（本报告） |

# W2 Task 1 报告：V3ArtifactVersion + helpers

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W2 — `V3ArtifactVersion` 模型与 `next_version` / `latest` helper

---

## What I Implemented

### 1. `V3ArtifactVersion` 模型

- `Status` 枚举：draft / candidate / committed / superseded
- 字段：`id`、`project`、`artifact_key`、`version`、`schema_version`（默认 1）、`status`、`payload`、`command_run`（nullable）、`created_at`
- `db_table = "drama_v3_artifact_version"`
- 唯一约束 `(project, artifact_key, version)` → `uniq_v3_artifact_version`

### 2. Helper `orchestrator/artifacts.py`

- `next_version(project_id, artifact_key) -> int`：无记录返回 1，否则 `max(version) + 1`
- `latest(project, artifact_key, status=None) -> V3ArtifactVersion | None`：按 `-version` 取首条；可选 `status` 过滤

### 3. 迁移 `0014_v3_artifact_version.py`

- 仅 `CreateModel V3ArtifactVersion`，无无关 RenameIndex

### 4. 测试 `test_v3_artifact.py`（6 用例）

- `test_create_candidate_artifact`
- `test_unique_project_key_version`
- `test_next_version_starts_at_one`
- `test_next_version_increments`
- `test_latest_returns_highest_version`
- `test_latest_filters_by_status`

---

## TDD: RED → GREEN

### Step 1–2: RED

**命令：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_artifact -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL

```
ImportError: cannot import name 'V3ArtifactVersion' from 'apps.drama.models'
```

### Step 3: 实现

- 修改 `backend/apps/drama/models.py`
- 新建 `backend/apps/drama/orchestrator/artifacts.py`
- `py -3 manage.py makemigrations drama --name v3_artifact_version`
- `py -3 manage.py migrate --settings=config.settings.sqlite_test`

### Step 4: GREEN

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_artifact -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS — 6 tests, OK (~3.6s)

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/models.py` | 修改（+ `V3ArtifactVersion`） |
| `backend/apps/drama/orchestrator/artifacts.py` | 新建 |
| `backend/apps/drama/migrations/0014_v3_artifact_version.py` | 新建 |
| `backend/apps/drama/tests/test_v3_artifact.py` | 新建 |
| `.superpowers/sdd/w2-task-1-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| 迁移无无关 RenameIndex | ✓ |
| 无新第三方库 | ✓ |
| 模型/ helper 对齐 W2 plan Task 1 | ✓ |
| 6/6 测试通过 | ✓ |

---

## Concerns / Follow-ups

- **Draft 独立表**：plan 标题含「可选 Draft」；W2 最小实现用 `status=draft` 行，未另建 `V3ArtifactDraft` 表（与 plan 正文一致）。
- **Admin**：`V3ArtifactVersion` 未注册 Django Admin；后续调试可按需补充。
- **Brief 文件**：`.superpowers/sdd/w2-task-1-brief.md` 不存在；实现依据 `docs/superpowers/plans/2026-07-23-drama-website-v3-w2-topic-blueprint.md` Task 1 节。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_artifact` | 6 | PASS |

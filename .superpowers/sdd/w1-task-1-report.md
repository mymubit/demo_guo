# W1 Task 1 报告：领域扩展 — 归档字段 + CommandRun

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 领域扩展（`archived_at` + `V3CommandRun`）

---

## What I Implemented

### 1. `V3Project.archived_at`

- 在 `V3Project` 增加 `archived_at = DateTimeField(null=True, blank=True, db_index=True)`。
- `None` 表示未归档；写入时间戳即视为已归档。

### 2. `V3CommandRun` 模型

- 新增 `V3CommandRun`，含 `Status` 枚举（queued / running / succeeded / failed / unsupported）。
- 字段：`id`、`owner`、`project`（nullable FK → V3Project）、`command_type`、`status`、`idempotency_key`、`request_payload`、`result_payload`、`error_message`、`created_at`、`updated_at`。
- `db_table = "drama_v3_command_run"`；索引 `(owner, -created_at)` 与 `(command_type, status)`。

### 3. 迁移 `0013_v3project_archived_at_v3commandrun.py`

- 仅含 `AddField archived_at` 与 `CreateModel V3CommandRun`。
- **未夹带** 无关 `RenameIndex` 操作。

### 4. 测试 `test_v3_domain_w1.py`

- `test_project_can_be_archived`：验证 `archived_at` 默认 `None`、可持久化。
- `test_command_run_defaults`：验证 `V3CommandRun` 创建与 `project=None` 默认。

---

## TDD: RED → GREEN

### Step 1–2: RED（失败测试）

**命令：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL

```
ImportError: cannot import name 'V3CommandRun' from 'apps.drama.models'
```

符合预期：`V3CommandRun` 与 `archived_at` 尚不存在。

### Step 3: 实现

- 修改 `backend/apps/drama/models.py`（`archived_at` + `V3CommandRun`）。
- `py -3 manage.py makemigrations drama` → 生成 `0013_v3project_archived_at_v3commandrun.py`。
- `py -3 manage.py migrate --settings=config.settings.sqlite_test`。

### Step 4: GREEN（通过测试）

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS

```
test_command_run_defaults ... ok
test_project_can_be_archived ... ok

Ran 2 tests in 0.752s
OK
```

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/models.py` | 修改（`archived_at` + `V3CommandRun`） |
| `backend/apps/drama/migrations/0013_v3project_archived_at_v3commandrun.py` | 新建 |
| `backend/apps/drama/tests/test_v3_domain_w1.py` | 新建 |
| `.superpowers/sdd/w1-task-1-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| 迁移无无关 RenameIndex | ✓ |
| 无新第三方库 | ✓ |
| 无 LLM / skills 调用 | ✓ |
| 模型风格对齐现有 drama models | ✓ |
| 测试全部通过 | ✓ |

---

## Concerns / Follow-ups

- **Admin 注册**：`V3CommandRun` 未注册 Django Admin；若 W1 后续任务需要后台查看，可在 Task 2+ 补充。
- **API 层**：本任务仅模型+迁移；归档与 CommandRun 的 REST/Command 端点留给后续 Task。
- **0012 历史迁移**：`0012_v3_project.py` 仍含 `RenameIndex`（W0 遗留）；本任务 0013 未再引入同类问题。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_domain_w1` | 2 | PASS |

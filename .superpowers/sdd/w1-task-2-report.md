# W1 Task 2 报告：编排器骨架（同步 create_project + 异步桩）

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W1 — 编排器骨架（`dispatch_command`）

---

## What I Implemented

### 1. `orchestrator/types.py`

- `SYNC_COMMANDS = frozenset({"create_project"})`
- `ASYNC_STUB_COMMANDS`：对齐 `docs/contracts/v3/commands.md`，除 `create_project` 外全部 14 条产品命令

### 2. `orchestrator/dispatcher.py`

- `dispatch_command(*, owner, command_type: str, payload: dict, idempotency_key: str = "") -> V3CommandRun`
- 流程：创建 `V3CommandRun`（`status=running`）→ 按类型分支 → 更新并返回
- **同步 `create_project`**：校验 `title` / `entry_type`（`original`|`adapt`），创建 `V3Project`（`stage=topic`），设 FK，`status=succeeded`，`result_payload={"project_id": "..."}`
- **异步白名单**：`status=unsupported`，`error_message` 含「后续里程碑开放」
- **未知命令**（如 `create-project-brief`）：`status=failed`，`error_message="未知命令"`
- 无 LLM / skills 导入

### 3. `orchestrator/__init__.py`

- 导出 `dispatch_command`

### 4. 测试 `test_v3_orchestrator.py`

- `test_create_project_succeeds_sync`：同步创建项目并关联 CommandRun
- `test_async_command_is_unsupported_stub`：`generate_topic_brief` → unsupported
- `test_unknown_command_fails`：`create-project-brief` → failed（非 unsupported）

---

## TDD: RED → GREEN

### Step 1–2: RED（失败测试）

**命令：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_orchestrator -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL

```
ModuleNotFoundError: No module named 'apps.drama.orchestrator'
```

符合预期：编排器包尚不存在。

### Step 3: 实现

- 新建 `backend/apps/drama/orchestrator/types.py`
- 新建 `backend/apps/drama/orchestrator/dispatcher.py`
- 新建 `backend/apps/drama/orchestrator/__init__.py`

### Step 4: GREEN（通过测试）

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_orchestrator -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS

```
test_async_command_is_unsupported_stub ... ok
test_create_project_succeeds_sync ... ok
test_unknown_command_fails ... ok

Ran 3 tests in 1.124s
OK
```

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/orchestrator/types.py` | 新建 |
| `backend/apps/drama/orchestrator/dispatcher.py` | 新建 |
| `backend/apps/drama/orchestrator/__init__.py` | 新建 |
| `backend/apps/drama/tests/test_v3_orchestrator.py` | 新建 |
| `.superpowers/sdd/w1-task-2-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| `dispatch_command` 签名与 brief 一致 | ✓ |
| `create_project` 同步成功路径 | ✓ |
| 14 条异步命令 → unsupported | ✓ |
| 未知类型 → failed（非 unsupported） | ✓ |
| 无 LLM / skills 调用 | ✓ |
| 测试全部通过 | ✓ |

---

## Concerns / Follow-ups

- **幂等键**：`idempotency_key` 已持久化，去重逻辑留给 W2+ API 层。
- **create_project 失败路径**：无效 payload 返回 `failed`，当前测试未覆盖；W2 API 接入时可补测。
- **confirm_* 同步命令**：契约标注为同步，W1 仍走 unsupported 桩；W2 实现时需从 `ASYNC_STUB_COMMANDS` 移出并单独实现。
- **API 层**：本任务仅编排器内核；REST Command 端点留给后续 Task。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_orchestrator` | 3 | PASS |

---

## Follow-up: create_project 事务原子性（2026-07-23）

**Issue:** `create_project` 路径先写 `V3CommandRun` 再写 `V3Project`，异常时可能留下半写状态（`running` 且无 project）。

**Fix:** `orchestrator/dispatcher.py` 中 `create_project` 分支整体包入 `transaction.atomic()`：`V3CommandRun` 创建、校验失败设 `failed`、成功创建 `V3Project` 并设 `succeeded` 均在同一原子块内提交。

**Re-test:** `py -3 manage.py test apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud -v 1 --settings=config.settings.sqlite_test` → **9 tests OK**

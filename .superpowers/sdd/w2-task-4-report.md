# W2 Task 4 报告：异步编排 + Celery 任务

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W2 — `ASYNC_LIVE` / `SYNC_CONFIRM` + Celery + confirm

---

## What I Implemented

### 1. `orchestrator/types.py`

- 从 `ASYNC_STUB_COMMANDS` 移除四条 W2 命令
- 新增 `ASYNC_LIVE_COMMANDS`：`generate_topic_brief` / `generate_blueprint`
- 新增 `SYNC_CONFIRM_COMMANDS`：`confirm_topic_brief` / `confirm_blueprint`

### 2. `orchestrator/dispatcher.py`

- live async：校验 `project_id` + 属主 → 创建 `queued` run → `enqueue_v3_command` → `refresh_from_db` 返回
- sync confirm：委托 `run_confirm_command`
- stub：仅剩余后续里程碑命令 → `unsupported`

### 3. `orchestrator/async_runner.py` + `tasks_v3.py`

- `enqueue_v3_command(run_id)` → Celery `run_v3_command_task.delay`
- `run_v3_command`：`running` → `execute_generation`（读 `settings.V3_LLM_CALL_OVERRIDE`）→ `succeeded` + `artifact_ids`；失败 → `failed` + 人话
- `config/celery.py`：`autodiscover_tasks(related_name="tasks_v3")`

### 4. `orchestrator/confirm.py`

- `confirm_topic_brief`：candidate→committed，旧 committed→superseded，`stage` topic→blueprint
- `confirm_blueprint`：五产物齐全才确认，否则 failed；`stage`→episodes
- 支持可选 `artifact_version_ids`；默认各 key 最新 candidate

### 5. 设置钩子

- `config/settings/base.py`：`V3_LLM_CALL_OVERRIDE = None`（测试可注入 callable）

### 6. executor 依赖门闩

- `execute_generation` 在缺 committed `project_brief` 时 raise `GenerationError("请先确认选题简报后再生成蓝图")`

### 7. 测试

- 新建 `test_v3_async_commands.py`（6 用例，eager + mock）
- 更新 `test_v3_orchestrator` stub 用例为仍 stub 的 `generate_episode_plan`

---

## TDD: RED → GREEN

### Step 1: RED

**命令：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_async_commands -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL（5）— W2 命令仍为 `unsupported`

### Step 2: 实现

- types / dispatcher / async_runner / tasks_v3 / confirm
- `V3_LLM_CALL_OVERRIDE` + celery `tasks_v3` 发现
- executor 依赖检查
- 修正 W1 orchestrator stub 断言命令

### Step 3: GREEN

**命令：**

```bash
py -3 manage.py test apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_skills_bridge -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS — 21 tests, OK (~6.5s)

```
test_confirm_blueprint_advances_to_episodes ... ok
test_confirm_topic_brief_commits_and_advances_stage ... ok
test_generate_blueprint_with_brief_writes_five_candidates ... ok
test_generate_blueprint_without_brief_fails_friendly ... ok
test_generate_topic_brief_eager_succeeds_with_candidate ... ok
test_no_v6_runtime_in_orchestrator_skills_bridge_tasks ... ok
(+ orchestrator 3 + skills_bridge 12)
```

**grep：**

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" apps/drama/orchestrator apps/drama/skills_bridge apps/drama/tasks_v3.py
```

Expected: 无匹配 ✓

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/orchestrator/types.py` | 修改 |
| `backend/apps/drama/orchestrator/dispatcher.py` | 修改 |
| `backend/apps/drama/orchestrator/async_runner.py` | 新建 |
| `backend/apps/drama/orchestrator/confirm.py` | 新建 |
| `backend/apps/drama/tasks_v3.py` | 新建 |
| `backend/apps/drama/skills_bridge/executor.py` | 修改（依赖门闩） |
| `backend/config/settings/base.py` | 修改（`V3_LLM_CALL_OVERRIDE`） |
| `backend/config/celery.py` | 修改（发现 `tasks_v3`） |
| `backend/apps/drama/tests/test_v3_async_commands.py` | 新建 |
| `backend/apps/drama/tests/test_v3_orchestrator.py` | 修改 |
| `.superpowers/sdd/w2-task-4-report.md` | 本报告 |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD（先测后实现，见 RED unsupported） | ✓ |
| ALWAYS_EAGER + `V3_LLM_CALL_OVERRIDE` mock | ✓ |
| confirm 同步；generate 异步 Celery | ✓ |
| 无 brief → failed 人话 | ✓ |
| grep 无 v6_runtime 等 | ✓ |
| 21/21 相关测试通过 | ✓ |

---

## Concerns / Follow-ups

- **eager 下返回态**：`dispatch` 在 enqueue 后 `refresh_from_db`；非 eager 仍为 `queued`，eager 测试可见终态 `succeeded/failed`。
- **confirm 与 draft**：W2 最小实现仅提交 candidate；draft 优先逻辑留给 Task 5。
- **任务边界异常**：`run_v3_command` 捕获宽异常并落库人话，避免 Celery worker 未处理崩溃把堆栈暴露给前端。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_async_commands` | 6 | PASS |
| `apps.drama.tests.test_v3_orchestrator` | 3 | PASS |
| `apps.drama.tests.test_v3_skills_bridge` | 12 | PASS |
| **合计** | **21** | **PASS** |

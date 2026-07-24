# W3 Task 1 报告：契约扩展 + V3ScriptDraft

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W3 — `confirm_episode_plan` 契约 + `V3ScriptDraft` 模型

---

## What I Implemented

### 1. 契约扩展 `confirm_episode_plan`

- `docs/contracts/v3/commands.md`：新增「确认分集规划」行；模块覆盖表同步
- `frontend/src/types/v3/commands.ts`：`PRODUCT_COMMAND_TYPES` 增加 `confirm_episode_plan`
- `frontend/src/types/v3/api.test.ts`：新增断言 `toContain('confirm_episode_plan')`

### 2. `V3ScriptDraft` 模型

- 字段：`id`（UUID PK）、`project`（FK V3Project）、`episode_number`、`payload`（JSONField）、`updated_at`（auto_now）
- `db_table = "drama_v3_script_draft"`
- 唯一约束 `(project, episode_number)` → `uniq_v3_project_episode_script_draft`
- `related_name="script_drafts"`

### 3. 迁移 `0015_v3_script_draft.py`

- 仅 `CreateModel V3ScriptDraft`，无无关操作

### 4. 测试 `test_v3_script_draft.py`（4 用例）

- `test_create_script_draft`
- `test_unique_project_episode`
- `test_update_or_create_overwrites_payload`
- `test_different_episodes_same_project_allowed`

---

## TDD: RED → GREEN

### Step 1: RED

**Backend：**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_script_draft -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL

```
ImportError: cannot import name 'V3ScriptDraft' from 'apps.drama.models'
```

**Frontend：**

```bash
cd frontend
npm test -- src/types/v3/api.test.ts
```

**结果：** FAIL — `expected [...] to include 'confirm_episode_plan'`

### Step 2–4: 实现 + GREEN

**Backend：**

```bash
py -3 manage.py makemigrations drama --name v3_script_draft
py -3 manage.py migrate --settings=config.settings.sqlite_test
py -3 manage.py test apps.drama.tests.test_v3_script_draft -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS — 4 tests, OK (~3.6s)

**Frontend：**

```bash
npm test -- src/types/v3/api.test.ts
```

**结果：** PASS — 2 tests, OK

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `docs/contracts/v3/commands.md` | 修改（+ `confirm_episode_plan`） |
| `frontend/src/types/v3/commands.ts` | 修改 |
| `frontend/src/types/v3/api.test.ts` | 修改 |
| `backend/apps/drama/models.py` | 修改（+ `V3ScriptDraft`） |
| `backend/apps/drama/migrations/0015_v3_script_draft.py` | 新建 |
| `backend/apps/drama/tests/test_v3_script_draft.py` | 新建 |
| `.superpowers/sdd/w3-task-1-report.md` | 本报告 |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| 迁移无无关 RenameIndex | ✓ |
| 无新第三方库 | ✓ |
| 模型对齐 W3 plan Task 1 接口 | ✓ |
| 契约三处同步（md / ts / test） | ✓ |
| 4/4 后端 + 2/2 前端测试通过 | ✓ |

---

## Concerns / Follow-ups

- **编排器未改**：`orchestrator/types.py` 仍无 `confirm_episode_plan`（属 Task 4）；当前仅契约与领域模型就绪。
- **OpenAPI 未改**：`openapi.yaml` 命令枚举留待 Task 5/6 API 落地时同步。
- **与 V6 `DramaScriptDraft` 并存**：V3 用 JSON `payload` 结构化场景；V6 仍用 `content` TextField，互不干扰。
- **Admin**：`V3ScriptDraft` 未注册 Django Admin；调试可按需补充。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_script_draft` | 4 | PASS |
| `src/types/v3/api.test.ts` | 2 | PASS |

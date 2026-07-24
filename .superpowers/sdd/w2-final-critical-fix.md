# W2 Final Critical Fix Report

**Date:** 2026-07-23  
**Status:** Done  
**Git commit:** 未提交（按要求）

## Problem

1. **Critical — 多候选残留：** `_commit_candidates` 仅把同 key 的旧 `committed` 标为 `superseded`，未清理其它 `candidate`。多次 generate 后 confirm 最新，仍可能残留旧 `candidate`；用旧 id 再 confirm 可能产生歧义。
2. **Important — 幂等作用域过宽：** `_find_reusable_idempotent_run` 只按 `(owner, idempotency_key)` 查找，不同 `command_type` 会错误复用同一 run。

## Changes

### 1. Confirm：提交时 supersede 同 key 全部其它 candidate

`backend/apps/drama/orchestrator/confirm.py` — `_commit_candidates`：

- 对每个待提交 key，将同 project + artifact_key、状态为 `committed` **或** `candidate` 的其它行（排除正在提交的 id）统一更新为 `SUPERSEDED`。
- 再将选中行置为 `COMMITTED`。

### 2. Generate：新建候选后 supersede 旧 candidate（preferred）

`backend/apps/drama/skills_bridge/executor.py` — `execute_generation`：

- 在同一事务内创建新 `candidate` 后，对本次 `writes` 各 key，将同 project + key 且 status=`candidate`、且不在本次创建 id 集合中的行标为 `SUPERSEDED`。

### 3. Idempotency：绑定 command_type

`backend/apps/drama/orchestrator/dispatcher.py` — `_find_reusable_idempotent_run`：

- 查找条件改为 `(owner, command_type, idempotency_key)` + 可复用状态（queued/running/succeeded）。
- `dispatch_command` 传入当前 `command_type`。

## Tests added

| Case | File |
|------|------|
| generate topic 两次 → confirm 最新 → 无残留 CANDIDATE；再 confirm 旧 id → FAILED 且旧行保持 SUPERSEDED | `test_v3_async_commands.test_generate_twice_confirm_latest_supersedes_prior_candidates` |
| 同 idempotency_key、不同 command_type 不复用 | `test_v3_idempotency.test_same_idempotency_key_different_command_type_not_reused` |

## Verification

```text
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test `
  apps.drama.tests.test_v3_async_commands `
  apps.drama.tests.test_v3_idempotency `
  apps.drama.tests.test_v3_topic_api `
  apps.drama.tests.test_v3_blueprint_api `
  -v 1 --settings=config.settings.sqlite_test
```

**Result:** `Ran 21 tests in ~16.6s — OK`

## Files touched

- `backend/apps/drama/orchestrator/confirm.py`
- `backend/apps/drama/orchestrator/dispatcher.py`
- `backend/apps/drama/skills_bridge/executor.py`
- `backend/apps/drama/tests/test_v3_async_commands.py`
- `backend/apps/drama/tests/test_v3_idempotency.py`
- `.superpowers/sdd/w2-final-critical-fix.md`（本报告）

## Notes

- 本地若 shell 预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库内 `drama-skills` 路径后再跑测。

# W4 Task 4 报告：编排 live + accept_findings + stage

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — 质检/交付命令 live 编排 + 同步 accept_findings + stage 推进  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. `orchestrator/types.py`

| 集合 | 变更 |
|------|------|
| `ASYNC_LIVE_COMMANDS` | + `score_quality` / `check_compliance` / `revise_from_findings` / `prepare_delivery` |
| `SYNC_MUTATION_COMMANDS` | 新建：`accept_findings` |
| `ASYNC_STUB_COMMANDS` | 仅保留 `test_model_provider` |

### 2. `orchestrator/accept_findings.py`（新建）

- 同步 upsert `V3QualityFinding`，`status=accepted`
- payload：`{ project_id, findings: [{ source, finding_key, title?, severity? }] }`
- 模块 docstring 对齐 `delivery_gate._blocking_issue_key`：`finding_key → id → title → blocking:{index}`
- `run_accept_findings_command`：与 confirm 同构的同步 run 入口（非 confirm）

### 3. `orchestrator/dispatcher.py`

- `SYNC_MUTATION_COMMANDS` → `run_accept_findings_command`
- live 命令走既有 enqueue 路径（无需特殊分支）

### 4. `orchestrator/async_runner.py`

- `requires_delivery_gate`：先 `evaluate_delivery_gate`；失败 → `failed` + 中文 blockers（`；` 拼接），**不调 LLM**
- 成功后 stage：`score_quality` / `check_compliance` 且 `writing` → `quality`；`prepare_delivery` → `delivery`
- `confirm_script_candidate` 未改：靠 stale，不删报告

### 5. 测试

| 文件 | 覆盖 |
|------|------|
| `test_v3_quality_async.py` | 双报告+stage；revise+confirm→stale 阻断；gate 失败不 LLM；gate 成功+delivery |
| `test_v3_accept_findings.py` | upsert accepted；空 findings 失败人话 |
| `test_v3_orchestrator` / `test_v3_projects_crud` | stub 断言改为 `test_model_provider` |

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_quality_async apps.drama.tests.test_v3_accept_findings apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud --settings=config.settings.sqlite_test -v 2
```

**结果：** PASS — **15 tests, OK**

回归：

```powershell
py -3 manage.py test apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_executor apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_async_commands --settings=config.settings.sqlite_test -v 1
```

**结果：** PASS — **29 tests, OK**

`rg v6_runtime|v6_workbench|v6_control_plane` 于 `orchestrator/`：无匹配。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/orchestrator/types.py` | 修改 |
| `backend/apps/drama/orchestrator/dispatcher.py` | 修改 |
| `backend/apps/drama/orchestrator/async_runner.py` | 修改 |
| `backend/apps/drama/orchestrator/accept_findings.py` | 新建 |
| `backend/apps/drama/tests/test_v3_quality_async.py` | 新建 |
| `backend/apps/drama/tests/test_v3_accept_findings.py` | 新建 |
| `backend/apps/drama/tests/test_v3_orchestrator.py` | 修改（stub 命令） |
| `backend/apps/drama/tests/test_v3_projects_crud.py` | 修改（stub 命令） |
| `.superpowers/sdd/w4-task-4-report.md` | 新建（本报告） |

未执行 git commit。未建 REST（Task 5/6）。

---

## Concerns / Follow-ups

- **UI finding_key：** 前端勾选合规阻断项时须用与 gate 相同键（优先 `finding_key`），否则 accept 后仍阻断交付。
- **REST：** Task 5/6 接线 `/quality/*`、`/delivery/*`；`/api/v3/commands/` 已可直接 dispatch live 命令。
- **独立 accept 编排测：** accept + gate 联通已由 Task 3 gate 测覆盖；本任务 accept 测侧重 upsert，未再开「accept 后 prepare 通过」编排用例。

---

## Reviewer Notes（自检）

- [x] 四命令移出 stub；`accept_findings` 同步
- [x] gate 先于 LLM；失败人话 blockers
- [x] writing→quality；prepare→delivery；confirm 靠 stale
- [x] finding_key 与 delivery_gate 对齐并文档化
- [x] ≥6 编排相关断言路径；Mock LLM；无 v6_*；无新依赖；无 commit

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

| 要求 | 结论 |
|------|------|
| 四命令 live（score/compliance/revise/prepare） | ✅ `ASYNC_LIVE_COMMANDS`；stub 仅 `test_model_provider` |
| `accept_findings` 同步 upsert | ✅ `SYNC_MUTATION_COMMANDS` + `run_accept_findings_command` |
| gate 先于 LLM | ✅ `recipe_map.requires_delivery_gate` → `evaluate_delivery_gate` 失败即 return |
| writing→quality / prepare→delivery | ✅ `_advance_stage_after_success` |
| confirm 靠 stale 不删报告 | ✅ 未改 confirm；`test_revise_confirm_makes_reports_stale` 覆盖 |
| finding_key 对齐 gate | ✅ docstring + gate `_blocking_issue_key` 一致 |
| ≥6 编排测 | ✅ 6（quality_async×4 + accept×2）；实测 15 tests OK |

**备注（非阻断）：** 无「accept 后 prepare 通过」端到端编排测；报告已标注，Task 3 gate 测部分覆盖。

**缺陷：** 无。

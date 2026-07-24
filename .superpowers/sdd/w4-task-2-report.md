# W4 Task 2 报告：recipe_map + fixtures + validate

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — 质检/交付配方映射、fixture 与 schema 校验  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. `skills_bridge/recipe_map.py`

新增四条 W4 配方：

| command_type | recipe_id | role | writes | commit_mode | requires_committed |
|---|---|---|---|---|---|
| `score_quality` | `score-script` | `drama-script-scorer` | `quality_report` | `direct` | `episode_scripts`, `episode_plan`, `project_brief` |
| `check_compliance` | `check-compliance` | `drama-compliance-guard` | `compliance_report` | `direct` | `episode_scripts`, `episode_plan`, `project_brief` |
| `revise_from_findings` | `revise-script` | `drama-revision-master` | `episode_scripts`, `memory_checkpoint` | `candidate` | `episode_scripts`, `episode_plan`, `story_bible` |
| `prepare_delivery` | `prepare-delivery` | `drama-delivery-tool` | `production_package` | `direct` + `requires_delivery_gate` | `episode_scripts`, `quality_report`, `compliance_report` |

**角色名对齐（skills 真相优先）：**

| 命令 | Plan 写的 role | Skills 真相 | 采用 |
|------|----------------|-------------|------|
| `score_quality` | `drama-score-critic` | `roles/drama-script-scorer` → `drama.script-scorer` / persona `script-scorer` | **`drama-script-scorer`**（偏离 plan） |
| `check_compliance` | `drama-compliance-guard` | `roles/drama-compliance-guard` | 一致 |
| `revise_from_findings` | `drama-revision-master` | `roles/drama-revision-master` | 一致 |
| `prepare_delivery` | `drama-delivery-tool` | `roles/drama-delivery-tool` | 一致 |

### 2. Fixtures（最小合法 JSON，对齐 V5 schema）

| 文件 | 产物 | Schema |
|------|------|--------|
| `tests/fixtures/v3_quality_report.json` | `quality_report` | `schemas/artifacts/quality_report/1.schema.json`（10 维均含 score/weight/evidence/deductions） |
| `tests/fixtures/v3_compliance_report.json` | `compliance_report` | `schemas/artifacts/compliance_report/1.schema.json` |
| `tests/fixtures/v3_production_package.json` | `production_package` | `schemas/artifacts/production_package/1.schema.json` |

均通过 `validate_artifact_payload`。

### 3. 测试扩展 `test_v3_skills_bridge.py`

- 配方断言 4 例（含 `commit_mode` / `requires_delivery_gate`）
- fixture validate 3 例
- `COMMAND_RECIPES` keys 集合更新为 9 个命令

未实现 executor / delivery_gate / API（留 Task 3+）。

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_skills_bridge --settings=config.settings.sqlite_test -v 2
```

**结果：** PASS — 26 tests, OK (~2.4s)

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/skills_bridge/recipe_map.py` | 修改 |
| `backend/apps/drama/tests/fixtures/v3_quality_report.json` | 新建 |
| `backend/apps/drama/tests/fixtures/v3_compliance_report.json` | 新建 |
| `backend/apps/drama/tests/fixtures/v3_production_package.json` | 新建 |
| `backend/apps/drama/tests/test_v3_skills_bridge.py` | 修改 |
| `.superpowers/sdd/w4-task-2-report.md` | 新建（本报告） |

未执行 git commit。

---

## Concerns / Follow-ups

- **`drama-score-critic` 偏离：** plan/brief 用词与 skills 目录不一致；已按 `drama-script-scorer` 落库，后续 Task 3 prompt 加载依赖此 role。
- **`commit_mode` / `requires_delivery_gate`：** 仅写入 recipe；executor 尚未识别（Task 3）。
- **V6 persona 别名：** operation 用 `persona.script-scorer` / `persona.delivery-producer`；V3 recipe 继续用目录式 `drama-*` role（与 W2/W3 一致），经 `_role_to_agent_id` 转 `drama.*`。
- **实质门禁：** `validate_artifact_payload` 仅 JSON Schema，不含 delivery/substance gates。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

**Spot-check:**
- `recipe_map.py`：四条 W4 配方字段与 brief 一致（`recipe_id` / `writes` / `requires_committed` / `commit_mode` / `requires_delivery_gate`）；`score_quality` 采用 `drama-script-scorer` 偏离 plan 的 `drama-score-critic`，但 skills 仅存在 `roles/drama-script-scorer` 且绑定 `operation.score-script`，可接受。
- Fixtures：`v3_quality_report.json` 十维均含 score/weight/evidence/deductions；三 fixture 经 `validate_artifact_payload` 断言通过。
- 测试：独立复跑 `test_v3_skills_bridge` — 26 tests OK；未越界实现 executor/gate。

**Notes:** plan/brief 中 `drama-score-critic` 为文档笔误，建议在 W4 plan 后续修订中对齐 skills 目录名。

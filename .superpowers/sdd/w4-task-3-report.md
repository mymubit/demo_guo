# W4 Task 3 报告：delivery_gate + executor direct-commit

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — 交付门禁 + 执行器 `commit_mode` direct/candidate  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. `orchestrator/delivery_gate.py`

`evaluate_delivery_gate(project) -> { passed: bool, blockers: list[str] }`：

| # | 规则 | 阻断文案 |
|---|------|----------|
| 1 | 无 committed `episode_scripts` | 「请先确认正文后再交付」（单独返回） |
| 2 | 无/过期 committed `quality_report` | 「需要有效的质量报告，请重新评分」 |
| 2b | 报告未过期但不通过 | 「质量报告未通过门禁」 |
| 3 | 无/过期 committed `compliance_report` | 「需要有效的合规报告，请重新审查」 |
| 3b | `overall_result != "通过"` | 「合规审查未通过」 |
| 4 | `blocking_issues` 非空且存在未 `accepted` 项 | 「存在未接受的合规阻断项，请先接受后再交付」 |
| 5 | 全部通过 | `passed=True`, `blockers=[]` |

质量通过条件（与 brief 一致）：

- `verdict in ("通过", "条件通过")` **或**
- `grade in ("S","A","B")` 且 `needs_revision is False`

过期判定复用 Task 1 `report_meta.is_report_stale`。

`blocking_issues` 键匹配顺序：`finding_key` → `id` → `title` → 回退 `blocking:{index}`；与 `V3QualityFinding(source=compliance, status=accepted)` 比对。空列表跳过。

### 2. `skills_bridge/executor.py` — `commit_mode`

- 读取 recipe `commit_mode`，默认 **`candidate`**（向后兼容）
- **`candidate`**：现有逻辑（写 candidate，仅 supersede 旧 candidate）
- **`direct`**：
  1. `strip_meta_for_validate` 后再 `validate_artifact_payload`
  2. 从最新 committed `episode_scripts` `attach_script_meta`
  3. 创建 **committed**
  4. supersede 同 key 旧 **committed + candidate**

未接线 dispatcher / async_runner / `requires_delivery_gate`（留 Task 4）。

### 3. 测试

| 文件 | 覆盖 |
|------|------|
| `test_v3_delivery_gate.py` | 缺正文 / 缺报告 / 过期 / 质量失败 / grade 带通过 / 合规失败 / 未接受阻断 / 已接受通过 / 空阻断跳过 / 全绿 |
| `test_v3_quality_executor.py` | score/compliance/prepare direct+meta；LLM 脏 meta 被覆盖；supersede；revise_from_findings 仍 candidate |

复用 Task 2 fixtures。

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_executor --settings=config.settings.sqlite_test -v 2
```

**结果：** PASS — **16 tests, OK** (~9.2s)

回归：

```powershell
py -3 manage.py test apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_report_meta --settings=config.settings.sqlite_test -v 1
```

**结果：** PASS — **38 tests, OK**

`rg v6_runtime|v6_workbench|v6_control_plane` 于本次改动路径：无匹配。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/orchestrator/delivery_gate.py` | 新建 |
| `backend/apps/drama/skills_bridge/executor.py` | 修改（commit_mode） |
| `backend/apps/drama/tests/test_v3_delivery_gate.py` | 新建 |
| `backend/apps/drama/tests/test_v3_quality_executor.py` | 新建 |
| `.superpowers/sdd/w4-task-3-report.md` | 新建（本报告） |

未执行 git commit。未改 dispatcher。

---

## Concerns / Follow-ups

- **`finding_key` 约定：** 门禁用 `finding_key|id|title|blocking:{i}`；Task 4 `accept_findings` / UI 勾选须产出相同键，否则已接受项对不上。
- **`prepare_delivery` 的 meta：** direct 路径对 `production_package` 也挂了 `_v3_meta`（与报告一致）；schema 校验前已 strip。若产品不需要包上溯源，可后续收窄为仅 quality/compliance。
- **`requires_delivery_gate`：** recipe 已标，执行器/编排尚未在入队前跑门禁（Task 4）。
- **stage 推进：** 仍未做（Task 4）。

---

## Reviewer Notes（自检）

- [x] 门禁规则与 brief 对齐
- [x] `is_report_stale` 复用 Task 1
- [x] direct/candidate 分叉；默认 candidate
- [x] 未接线 dispatcher
- [x] Mock LLM；无 v6_*；无新依赖；无 commit

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

**Spot-check:**
- `delivery_gate.py`：5 条门禁与 brief/plan 伪代码一致；缺正文早退；质量/合规 stale 用 Task 1 `is_report_stale`；`_quality_passes` 覆盖 verdict / grade+needs_revision；`blocking_issues` 空列表跳过、键序 `finding_key→id→title→blocking:{i}` 与 `V3QualityFinding(COMPLIANCE, accepted)` 比对。
- `executor.py`：`commit_mode` 默认 `candidate`；`direct` 路径 strip→validate→`attach_script_meta`→committed→supersede 旧 committed+candidate；`revise_from_findings` 仍 candidate；未接线 dispatcher/async。
- 测试：独立复跑 Task 3 — 16 OK；回归 38 OK。

**Notes (Minor):** 缺 `test_stale_compliance_report_blocks`（仅有 quality stale）；`prepare_delivery` 对 `production_package` 也挂 `_v3_meta`（报告已标注，Task 4 前可接受）。

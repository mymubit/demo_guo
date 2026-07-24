# W4 Task 1 报告：契约说明 + V3QualityFinding + report meta 约定

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — `V3QualityFinding` 模型 + `report_meta` + Quality/Delivery 契约类型  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. 契约说明 `docs/contracts/v3/commands.md`

新增「质检 / 交付执行约定（W4）」：

- `accept_findings`：**同步**（无 LLM、无候选确认）
- `score_quality` / `check_compliance` / `prepare_delivery`：异步 direct-commit；**无**独立 confirm
- `revise_from_findings`：候选确认沿用 `confirm_script_candidate`
- 报告 `_v3_meta.source_script_version` 与 `is_stale` 语义简述

### 2. OpenAPI `docs/contracts/v3/openapi.yaml`

新增 schemas（本任务不挂 path，API 留 Task 5/6）：

- `QualityFinding`
- `QualityState`（含 `quality_is_stale` / `compliance_is_stale`）
- `DeliveryGateSnapshot` / `DeliveryState`
- `EnvelopeQualityState` / `EnvelopeDeliveryState`

### 3. 前端类型 `frontend/src/types/v3/domain.ts`

- `QualityFindingSource` / `QualityFindingStatus` / `QualityFinding`
- `QualityState` / `DeliveryGateSnapshot` / `DeliveryState`

`commands.ts` 无需改动（W0 已含 `score_quality` / `accept_findings` 等）。

### 4. 模型 `V3QualityFinding` + migration `0016`

字段与 brief 接口逐字对齐：

| 字段 | 说明 |
|------|------|
| `source` | `quality` / `compliance` |
| `finding_key` | 稳定键，max 128 |
| `status` | `open` / `accepted` / `resolved`（默认 open） |
| `report_artifact` | FK → `V3ArtifactVersion`，SET_NULL，可空 |
| 唯一约束 | `(project, source, finding_key)` → `uniq_v3_finding_project_source_key` |
| `db_table` | `drama_v3_quality_finding` |

迁移：`backend/apps/drama/migrations/0016_v3_quality_finding.py`（依赖 `0015_v3_script_draft`）。

### 5. `orchestrator/report_meta.py`

| 符号 | 行为 |
|------|------|
| `META_KEY = "_v3_meta"` | 约定键 |
| `attach_script_meta` | 写入 `source_script_version` + `source_script_artifact_id`（不改入参） |
| `strip_meta_for_validate` | 剥离 meta 供 schema 校验 |
| `read_source_script_version` | 读 int 或 None |
| `is_report_stale` | `current_script.version ≠ source_script_version` → True；无正文/无 meta → True |

---

## TDD: RED → GREEN

### Step 1: RED

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_quality_finding apps.drama.tests.test_v3_report_meta --settings=config.settings.sqlite_test -v 2
```

**结果：** FAIL（errors=2）

- `ImportError: cannot import name 'V3QualityFinding'`
- `ModuleNotFoundError: No module named 'apps.drama.orchestrator.report_meta'`

### Step 2–3: 实现 + GREEN

同命令复跑。

**结果：** PASS — **11 tests, OK** (~4.8s)

| 模块 | 用例 |
|------|------|
| `test_v3_quality_finding` | create / unique 约束 / 同 key 不同 source / report_artifact FK |
| `test_v3_report_meta` | attach 形状 / strip / read / stale false / stale true（升版、无正文、无 meta） |

---

## Self-Review

### 对齐检查

- [x] 模型接口与 brief 逐字段一致
- [x] 迁移编号 `0016`，依赖 `0015`
- [x] 未引入 v6_runtime / v6_workbench / v6_control_plane
- [x] 未引入新第三方库
- [x] 未 commit
- [x] 无 API / executor（本任务边界）

### Concerns（非阻塞）

1. **OpenAPI 仅 schemas、无 path**：符合「本任务无 API」；Task 5/6 需挂 `/quality/`、`/delivery/`。
2. **`is_report_stale` 边界**：无 `current_script` 或无 `_v3_meta` 时返回 `True`（偏门禁安全）；计划字面「iff ≠」在缺失值上未规定，后续若需「缺失=不过期」再改。
3. **`report_artifact` 未设 `related_name`**：与 brief 一致；反向查询时用默认 `v3qualityfinding_set`。

### 风险

低。纯模型 + 纯函数 + 契约类型，无运行时入口变更。

---

## Files Touched

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/models.py` | 新增 `V3QualityFinding` |
| `backend/apps/drama/migrations/0016_v3_quality_finding.py` | 新建 |
| `backend/apps/drama/orchestrator/report_meta.py` | 新建 |
| `backend/apps/drama/tests/test_v3_quality_finding.py` | 新建 |
| `backend/apps/drama/tests/test_v3_report_meta.py` | 新建 |
| `docs/contracts/v3/commands.md` | 质检/交付约定 |
| `docs/contracts/v3/openapi.yaml` | Quality/Delivery schemas |
| `frontend/src/types/v3/domain.ts` | TS 类型 |

---

## Follow-ups（后续 Task）

- Task 2：recipe_map + fixtures
- Task 5/6：挂 OpenAPI paths + REST 实现 `QualityState` / `DeliveryState`

---

## Reviewer Verdict

**Spec compliance:** ✅

- `V3QualityFinding` 字段、约束、`db_table` 与 brief 逐字一致；迁移 `0016` 依赖 `0015` 正确。
- `orchestrator/report_meta.py` 五符号签名与 meta JSON 形状符合约定；`attach`/`strip` 不修改入参。
- 契约：`commands.md` 已注明 `accept_findings` 同步及报告类命令无 confirm；OpenAPI / `domain.ts` 含 Quality/Delivery schemas。
- 测试 11/11 通过（reviewer 独立复跑）；无 v6_runtime/workbench/control_plane、无新第三方库、无 commit。
- 无 spec gap。

**Task quality:** **Approved**

- **Critical:** 无
- **Important:** 无
- **Minor:** `is_report_stale` 在 `current_script=None` 或无 `_v3_meta` 时返回 `True`（fail-safe）；brief 字面「iff ≠」未规定缺失值，实现者已在 Concerns 中说明，可接受。

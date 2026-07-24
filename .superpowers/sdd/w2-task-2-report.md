# W2 Task 2 报告：skills_bridge 配方映射 + 校验（无 LLM）

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W2 — `skills_bridge` recipe_map + validate

---

## What I Implemented

### 1. `skills_bridge/recipe_map.py`

- `COMMAND_RECIPES`：`generate_topic_brief` → `project_brief`；`generate_blueprint` → 5 产物
- `recipe_for(command_type)`：返回配方副本；未知命令 `KeyError`

### 2. `skills_bridge/validate.py`

- `validate_artifact_payload(artifact_key, payload) -> list[str]`
- Schema 路径解析顺序（均经 `skills_loader.root`，无第二 schema root）：
  1. `contracts/artifacts.yaml` 的 `schema_path`（V5 产物如 `project_brief`）
  2. V6 catalog `get_artifact_contract` 的 `schema_path` / `schema`
  3. `v6/manifest.yaml` `components` 段（如 `originality_report`）
- 校验复用 `SchemaValidator` + `Draft202012Validator.iter_errors`

### 3. Fixture

- `tests/fixtures/v3_project_brief_candidate.json` — 自 `schemas/artifacts/project_brief/1.schema.json` 必填字段构造的最小合法样例

### 4. 测试 `test_v3_skills_bridge.py`（7 用例）

- 配方映射 4 例 + 校验 3 例

---

## TDD: RED → GREEN

### Step 1: RED

**命令：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_skills_bridge -v 2 --settings=config.settings.sqlite_test
```

**结果：** FAIL

```
ModuleNotFoundError: No module named 'apps.drama.skills_bridge'
```

### Step 2–3: 实现

- 新建 `backend/apps/drama/skills_bridge/__init__.py`
- 新建 `recipe_map.py`、`validate.py`
- 新建 fixture 与测试

### Step 4: GREEN

**命令：** 同上

**结果：** PASS — 7 tests, OK (~0.03s)

```
test_command_recipes_keys ... ok
test_generate_blueprint_writes_five_artifacts ... ok
test_generate_topic_brief_writes_project_brief ... ok
test_unknown_command_raises ... ok
test_fixture_payload_passes ... ok
test_invalid_payload_returns_errors ... ok
test_unknown_artifact_key_returns_error ... ok
```

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/skills_bridge/__init__.py` | 新建 |
| `backend/apps/drama/skills_bridge/recipe_map.py` | 新建 |
| `backend/apps/drama/skills_bridge/validate.py` | 新建 |
| `backend/apps/drama/tests/fixtures/v3_project_brief_candidate.json` | 新建 |
| `backend/apps/drama/tests/test_v3_skills_bridge.py` | 新建 |
| `.superpowers/sdd/w2-task-2-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| 无 LLM 调用 | ✓ |
| 无 v6_runtime / v6_workbench / v6_control_plane 引用 | ✓ |
| Schema 经 skills_loader / SchemaValidator | ✓ |
| 7/7 测试通过 | ✓ |

---

## Concerns / Follow-ups

- **V5 vs V6 schema 优先级**：`project_brief` 优先走 `contracts/artifacts.yaml`（V5 `schemas/artifacts/...`），与 W2 plan 一致；V6 catalog 中的同名产物 schema 更严格，W2 暂以 V5 为准。
- **`originality_report`**：不在 V6 catalog `artifacts` 段，经 `v6/manifest.yaml` `components` 解析 schema；Task 3 executor 写 blueprint 时需准备对应 fixture。
- **实质门禁**：`validate_artifact_payload` 仅 JSON Schema，不含 `substance_gates`（Task 4+ 可按需叠加）。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_skills_bridge` | 7 | PASS |

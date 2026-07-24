# W2 Task 3 报告：LLM executor（可注入 mock）

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W2 — `skills_bridge/executor.py` + fake `llm_call` 测试

---

## What I Implemented

### 1. `skills_bridge/executor.py`

- `GenerationError`：校验 / JSON / Provider 失败统一异常
- `execute_generation(command_type, project, run, llm_call=None) -> list[V3ArtifactVersion]`
  1. `recipe_for`
  2. 最小 prompt：`loader.load_skill(agent_id)` 前 2000 字 + 项目 title/entry_type + committed 依赖
  3. `llm_call(prompt)`；默认 `_default_llm_call` 走 `LlmProvider`（未启用则人话「请先在模型配置中配置并启用供应商」）
  4. 单 write：整包 JSON；多 write：按键拆分
  5. `validate_artifact_payload`；失败 raise，不落库
  6. 事务内创建 `status=candidate` 版本（`next_version`）

### 2. Schema 路径修复

- `SchemaValidator._resolve_path`：支持 `v6/...` 相对 skills_root（否则组件 schema 被错误拼到 `schemas/v6/...`）

### 3. Fixture

- `tests/fixtures/v3_blueprint_bundle.json`：五键  
  `story_bible`（V5 valid）+ `character_system` / `world_system` / `emotion_system` / `originality_report`（V6 valid fixtures）

### 4. 测试扩展 `test_v3_skills_bridge.py`

- 校验：blueprint 五组件 fixture 通过
- executor：topic 1 candidate / blueprint 5 candidates / 非法 payload / 无 Provider 人话错误  
- 全部经 fake `llm_call`，不触网

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
ModuleNotFoundError: No module named 'apps.drama.skills_bridge.executor'
```

### Step 2: 实现

- 新建 `executor.py`
- 新建 blueprint fixture
- 修复 `SchemaValidator._resolve_path`（`v6/`）
- 扩展测试

### Step 3: GREEN

**命令：** 同上

**结果：** PASS — 12 tests, OK (~1.7s)

```
test_default_llm_without_provider_raises_friendly_error ... ok
test_generate_blueprint_writes_five_candidates ... ok
test_generate_topic_brief_writes_one_candidate ... ok
test_invalid_payload_raises_generation_error ... ok
test_command_recipes_keys ... ok
test_generate_blueprint_writes_five_artifacts ... ok
test_generate_topic_brief_writes_project_brief ... ok
test_unknown_command_raises ... ok
test_blueprint_component_fixtures_pass ... ok
test_fixture_payload_passes ... ok
test_invalid_payload_returns_errors ... ok
test_unknown_artifact_key_returns_error ... ok
```

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/skills_bridge/executor.py` | 新建 |
| `backend/apps/drama/skills_bridge/__init__.py` | 修改（模块说明） |
| `backend/apps/core/schema_validator.py` | 修改（`v6/` 路径） |
| `backend/apps/drama/tests/fixtures/v3_blueprint_bundle.json` | 新建 |
| `backend/apps/drama/tests/test_v3_skills_bridge.py` | 扩展 |
| `.superpowers/sdd/w2-task-3-report.md` | 本报告 |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD（先测后实现，见 RED ImportError） | ✓ |
| 测试用 fake `llm_call`，不触网 | ✓ |
| 角色 SKILL 从 drama-skills 加载，未硬编码正文 | ✓ |
| 无 `v6_runtime` / `v6_workbench` / `v6_control_plane` | ✓ |
| 无 Provider → 人话错误文案 | ✓ |
| 12/12 测试通过 | ✓ |

---

## Concerns / Follow-ups

- **`story_bible` schema 双轨**：校验仍优先 V5 `contracts/artifacts.yaml`；blueprint fixture 的 `story_bible` 用 V5 形态，组件四键用 V6。若后续统一到 V6 story-bible schema，需同步改 validate 优先级与 fixture。
- **Prompt 极简**：仅 SKILL 前缀 + JSON 用户上下文，无完整 injection（符合 W2）；Task 4+ 可经 `V3_LLM_CALL_OVERRIDE` 注入。
- **默认 Provider 路径**：测试覆盖「未启用」分支；成功调用路径依赖真实/ mock Provider，留给集成测。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_skills_bridge` | 12 | PASS |

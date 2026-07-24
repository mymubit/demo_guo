# W3 Task 2 报告：recipe_map + fixtures + validate 覆盖

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W3 — 分集/正文配方映射、fixture 与校验

---

## What I Implemented

### 1. `skills_bridge/recipe_map.py`

新增三条 W3 配方，并为全部命令补齐 `requires_committed`：

| command_type | recipe_id | role | writes | requires_committed |
|---|---|---|---|---|
| `generate_episode_plan` | `design-episode-plan` | `drama-episode-designer` | `episode_plan` | `project_brief`, `story_bible` |
| `revise_episode_plan` | `revise-episode-plan` | `drama-episode-designer` | `episode_plan` | `episode_plan` |
| `write_episode_batch` | `write-episodes` | `drama-script-writer` | `episode_scripts`, `memory_checkpoint` | `episode_plan`, `story_bible`, `project_brief` |

W2 命令同步声明 `requires_committed`（`generate_topic_brief` → `[]`，`generate_blueprint` → `["project_brief"]`）。

### 2. `skills_bridge/executor.py`

- 移除硬编码 `_COMMAND_READS`
- 新增 `_required_committed_keys(recipe)`，从配方读取 `requires_committed`
- `_ensure_committed_dependencies` / `_build_prompt` 均改为读 recipe
- 补充 `story_bible`、`episode_plan` 依赖提示文案

### 3. Fixtures（最小合法 JSON，对齐 schema）

| 文件 | 产物 | Schema 来源 |
|------|------|-------------|
| `tests/fixtures/v3_episode_plan_candidate.json` | `episode_plan` | `v6/artifacts/episode-plan/2.schema.json` |
| `tests/fixtures/v3_episode_scripts_candidate.json` | `episode_scripts` | `schemas/artifacts/episode_scripts/1.schema.json`（含内嵌 checkpoint） |
| `tests/fixtures/v3_memory_checkpoint_candidate.json` | `memory_checkpoint` | `schemas/artifacts/memory_checkpoint/1.schema.json` |

### 4. 测试 `test_v3_skills_bridge.py`（19 用例）

新增：
- 配方映射 3 例（`generate_episode_plan` / `revise_episode_plan` / `write_episode_batch`）
- validate fixture 3 例
- executor 依赖门禁 1 例（缺 committed 蓝图 → `GenerationError`）

### 5. 阻塞修复：`orchestrator/__init__.py`

W3 新增 orchestrator 包 eager import `dispatcher` 导致与 `executor` 循环导入，测试无法加载。改为 `__getattr__` 懒加载 `dispatch_command`，解除循环。

---

## TDD: RED → GREEN

### Step 1: RED（配方断言）

扩展 `RecipeMapTests` / `ValidateArtifactPayloadTests` 后，因循环导入无法加载模块。

### Step 2–3: 实现

- 更新 `recipe_map.py`、`executor.py`
- 新建 3 个 fixture
- 扩展测试
- 修复 orchestrator 循环导入

### Step 4: GREEN

**命令：**

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_skills_bridge -v 2 --settings=config.settings.sqlite_test
```

**结果：** PASS — 19 tests, OK (~2.1s)

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `backend/apps/drama/skills_bridge/recipe_map.py` | 修改 |
| `backend/apps/drama/skills_bridge/executor.py` | 修改 |
| `backend/apps/drama/orchestrator/__init__.py` | 修改（循环导入修复） |
| `backend/apps/drama/tests/fixtures/v3_episode_plan_candidate.json` | 新建 |
| `backend/apps/drama/tests/fixtures/v3_episode_scripts_candidate.json` | 新建 |
| `backend/apps/drama/tests/fixtures/v3_memory_checkpoint_candidate.json` | 新建 |
| `backend/apps/drama/tests/test_v3_skills_bridge.py` | 修改 |
| `.superpowers/sdd/w3-task-2-report.md` | 新建（本报告） |

未执行 git commit。

---

## Self-Review

| 检查项 | 状态 |
|--------|------|
| TDD 顺序（先测后实现） | ✓ |
| 无 LLM 网络调用 | ✓ |
| 无 v6_runtime / v6_workbench / v6_control_plane 引用 | ✓ |
| `requires_committed` 从 recipe 读取 | ✓ |
| 19/19 测试通过 | ✓ |

---

## Concerns / Follow-ups

- **V5 vs V6 schema 分裂**：`episode_plan` 走 V6 schema；`episode_scripts` / `memory_checkpoint` 仍走 V5 `schemas/artifacts/...`（与 `contracts/artifacts.yaml` 一致）。Task 3 executor 写正文时需按 V5 形态组装双产物返回。
- **`write_episode_batch` 双写**：executor 当前 `_map_payloads` 已支持多 key 拆分，但合并/局部 revise 逻辑留 Task 3。
- **实质门禁**：`validate_artifact_payload` 仅 JSON Schema，不含 substance_gates。
- **循环导入**：若后续在 `orchestrator/__init__.py` 增加更多 eager import，需保持懒加载或拆分包结构。

---

## Test Summary

| 套件 | 用例数 | 结果 |
|------|--------|------|
| `apps.drama.tests.test_v3_skills_bridge` | 19 | PASS |

# V3 W3 分集 + 正文 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通「确认蓝图 → 生成/确认分集规划 → 分批写正文 → 确认脚本候选」主链中段，使至少一批正文可编辑并以候选确认方式落正式版。

**Architecture:** 复用 W2 的 `skills_bridge` + Celery + `V3ArtifactVersion` 候选/确认模式。新增配方 `generate_episode_plan` / `revise_episode_plan` / `write_episode_batch`；正文人工草稿用 `V3ScriptDraft`（按集号），与 AI `episode_scripts` 候选分离。前端分集看板 + 简易结构化编辑器（**本里程碑不引入 Tiptap**，见下方理由）。

**Tech Stack:** 同 W2；LLM 测试必须 mock；`CELERY_TASK_ALWAYS_EAGER`

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§4–5 分集/正文）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W2 已通过（含 candidate supersede 修复）

## 编辑器选型（Global）

**本里程碑不引入 Tiptap/ProseMirror。**  
理由：仓库 `frontend/package.json` 尚无编辑器依赖；用户规范禁止随意加第三方库；W3 验收是「至少一批正文确认落库」，结构化 JSON（场景列表 + 对白/动作字段）+ textarea 即可闭环。Tiptap 留到正文交互稳定后的独立 polish 计划再论证版本与节点 schema。

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / 配方 ID
- **禁止** `v6_runtime` / `v6_workbench` / `v6_control_plane`
- 复用 `execute_generation` / `confirm` / supersede 语义；生成成功须淘汰同 key 旧 candidate
- 单元测试 mock LLM；禁止外网
- 不引入新第三方库（含 Tiptap）
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- 确认蓝图（`stage=episodes`）后方可生成分集；确认分集后方可写正文

## 命令扩展（须同步 `docs/contracts/v3/commands.md` + `commands.ts`）

| command_type | 模式 | 行为 |
|--------------|------|------|
| `generate_episode_plan` | 异步 | 依赖 committed 蓝图组 → 候选 `episode_plan` |
| `confirm_episode_plan` | 同步 | **新增**；candidate→committed；`stage=writing` |
| `revise_episode_plan` | 异步 | payload 含 `episode_numbers: int[]`；只改范围内卡片；产出新 candidate |
| `write_episode_batch` | 异步 | payload `episode_range: {start,end}`；写 `episode_scripts` + `memory_checkpoint` 候选 |
| `confirm_script_candidate` | 同步 | 确认脚本候选；可选推进进度；不强制改 stage（可留在 writing） |

从 `ASYNC_STUB_COMMANDS` 移除以上 live 命令；其余仍 stub。

## File Map

| 职责 | 路径 |
|------|------|
| 脚本草稿 | `models.py` → `V3ScriptDraft` |
| 配方 | `skills_bridge/recipe_map.py` |
| 确认 | `orchestrator/confirm.py` 扩展 |
| 类型 | `orchestrator/types.py`、`dispatcher.py` |
| API | `api/v3/episodes_views.py`、`scripts_views.py` |
| 契约 | `docs/contracts/v3/commands.md`、`openapi.yaml`、`frontend/src/types/v3/commands.ts` |
| 前端 | `pages/EpisodesPage.tsx`、`pages/ScriptEditorPage.tsx`、`services/v3/episodes.ts`、`scripts.ts` |
| 路由 | `app/router.tsx`：`/projects/:id/episodes`、`/projects/:id/editor` |
| Fixture | `tests/fixtures/v3_episode_plan_candidate.json`、`v3_episode_scripts_batch.json` |
| 测试 | `test_v3_episodes_*`、`test_v3_scripts_*`；前端对应 `*.test.tsx` |

## W3 验收标准

1. 蓝图已确认项目可生成分集规划候选并确认；`stage=writing`
2. 可对指定集数范围 `revise_episode_plan` 产生新候选（全剧其它集保持）
3. 可对第 1–N 集（N≥1，测试用 1–2）`write_episode_batch` 得到 `episode_scripts` 候选
4. 可确认脚本候选；正文可在编辑器保存草稿且不覆盖 committed，直到再次确认策略明确（W3：草稿独立；确认只提交 AI candidate 或「用草稿覆盖再 committed」二选一，见 Task 6）
5. UI：分集看板 + 编辑器；无 operation ID
6. 回归 W0–W2 测试仍绿；新增测全 mock LLM
7. grep 新代码无 `v6_runtime`

---

### Task 1: 契约扩展 + `V3ScriptDraft`

**Files:**
- Modify: `docs/contracts/v3/commands.md`、`frontend/src/types/v3/commands.ts`、`api.test.ts`（枚举含新命令）
- Modify: `models.py` + migration
- Test: `test_v3_script_draft.py`

**Interfaces — ScriptDraft:**

```python
class V3ScriptDraft(models.Model):
    id = UUID PK
    project = FK V3Project
    episode_number = PositiveIntegerField
    payload = JSONField  # {scenes: [{id, heading, beats:[{type, text, character?}]}]}
    updated_at = auto_now
    Meta: unique (project, episode_number)
```

- [ ] **Step 1: 失败测试** — 缺模型；commands 枚举缺 `confirm_episode_plan`

- [ ] **Step 2–4: 实现至 PASS**；`PRODUCT_COMMAND_TYPES` 增加 `confirm_episode_plan`

---

### Task 2: recipe_map + fixtures + validate 覆盖

**Files:**
- Modify: `skills_bridge/recipe_map.py`
- Create fixtures for `episode_plan`、`episode_scripts`、`memory_checkpoint`（最小合法 JSON，对齐 schema）
- Extend: `test_v3_skills_bridge.py`

**Interfaces:**

```python
"generate_episode_plan": {
  "recipe_id": "design-episode-plan",
  "role": "drama-episode-designer",
  "writes": ["episode_plan"],
  "requires_committed": ["project_brief", "story_bible"],  # 至少 brief+bible；实现时可要求蓝图五件套中的 bible
},
"revise_episode_plan": {
  "recipe_id": "revise-episode-plan",
  "role": "drama-episode-designer",
  "writes": ["episode_plan"],
  "requires_committed": ["episode_plan"],
},
"write_episode_batch": {
  "recipe_id": "write-episodes",
  "role": "drama-script-writer",
  "writes": ["episode_scripts", "memory_checkpoint"],
  "requires_committed": ["episode_plan", "story_bible", "project_brief"],
},
```

- [ ] **Step 1–4: TDD** — `recipe_for` 断言；fixture 通过 `validate_artifact_payload`

**依赖检查：** 扩展 `executor._ensure_committed_dependencies` 读取 recipe 的 `requires_committed`（若尚硬编码则改为读 recipe）。

---

### Task 3: executor 支持分集/正文 JSON 形态

**Files:**
- Modify: `skills_bridge/executor.py`
- Test: extend skills_bridge / 新 `test_v3_episode_executor.py`

**约定（mock LLM 返回）：**
- `generate_episode_plan` / `revise_episode_plan`：单对象 = `episode_plan` payload  
- `write_episode_batch`：

```json
{
  "episode_scripts": { "episodes": [ ... ] },
  "memory_checkpoint": { ... }
}
```

`revise_episode_plan`：executor 将 LLM 返回的局部 episodes **合并**进已有 committed plan 的拷贝后再 validate（合并逻辑单测覆盖：范围外卡片不变）。

- [ ] **Step 1–4: fake llm_call TDD 至 PASS**

---

### Task 4: 编排 live 命令 + confirm_episode_plan / confirm_script_candidate

**Files:**
- Modify: `orchestrator/types.py`、`dispatcher.py`、`confirm.py`、`async_runner.py`
- Test: `test_v3_episodes_async.py`

**语义：**
- `generate_episode_plan`：无 committed 蓝图（至少 `story_bible`+`project_brief`，推荐检查 blueprint 五件已确认或 `stage in (episodes,writing,...)`）→ failed 人话
- `confirm_episode_plan`：supersede 旧 candidate；`stage=writing`（仅当当前为 episodes）
- `write_episode_batch`：校验 `episode_range`；缺分集计划 → failed
- `confirm_script_candidate`：提交 `episode_scripts`（及同 run 的 `memory_checkpoint`）；supersede 旧候选
- 继续使用 `V3_LLM_CALL_OVERRIDE` + eager

- [ ] **Step 1: 测试用例**
  1. 无蓝图生成分集 → failed  
  2. 有蓝图 → generate plan → confirm → stage writing  
  3. revise 仅改 ep 2 → 其它集不变  
  4. write 1–2 → 两产物 candidate  
  5. confirm scripts → committed  
  6. 双 generate plan → confirm 后无残留 candidate（回归 supersede）

- [ ] **Step 2–4: 实现 PASS**

---

### Task 5: Episodes REST API

**Files:**
- Create: `api/v3/episodes_views.py`
- Modify: `urls.py`、`serializers.py`、`openapi.yaml`
- Test: `test_v3_episodes_api.py`

**Interfaces:**

```
GET  /api/v3/projects/{id}/episodes/
  → { stage, committed, candidate, latest_run }

POST /api/v3/projects/{id}/episodes/generate/
  body: { episode_count?: int, duration_target?: str, planning_requests?: object }

POST /api/v3/projects/{id}/episodes/confirm/

POST /api/v3/projects/{id}/episodes/revise/
  body: { episode_numbers: int[], revision_requests?: object }
```

Owner 隔离；generate/revise → dispatch；confirm → `confirm_episode_plan`。

- [ ] **Step 1–4: TDD API + OpenAPI**

---

### Task 6: Scripts REST API + 草稿

**Files:**
- Create: `api/v3/scripts_views.py`
- Test: `test_v3_scripts_api.py`

**Interfaces:**

```
GET  /api/v3/projects/{id}/scripts/
  → { committed, candidate, drafts: [{episode_number, payload, updated_at}], latest_run }

GET  /api/v3/projects/{id}/scripts/{episode_number}/
  → 单集视图：committed 切片 + draft + candidate 切片

PUT  /api/v3/projects/{id}/scripts/{episode_number}/draft/
  body: { payload }

POST /api/v3/projects/{id}/scripts/generate/
  body: { start: int, end: int, writing_requests?: object }

POST /api/v3/projects/{id}/scripts/confirm/
  body: { use_drafts?: bool }
  # use_drafts=true：将各集 draft 合并进 scripts 结构后作为新 committed（须 validate）；否则确认 AI candidate
```

- [ ] **Step 1–4: TDD**；`use_drafts` 路径必须跑 `validate_artifact_payload("episode_scripts", ...)`（消化 W2 draft 未校验债）

---

### Task 7: 前端分集看板

**Files:**
- Create: `pages/EpisodesPage.tsx`、`services/v3/episodes.ts`、测试
- Modify: `router.tsx`、`ProjectOverviewPage` CTA（stage=episodes → 去分集；writing → 可去编辑器）

**UI（中文）：**
- 卡片/列表展示每集标题、钩子、情绪（有字段则显示，否则折叠 JSON）
- 「生成全剧规划」「确认采用」「局部修订」（多选集合）
- 轮询 run；无 operation ID
- 无蓝图时禁用并链到 blueprint

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 8: 前端正文编辑器（结构化，非 Tiptap）

**Files:**
- Create: `pages/ScriptEditorPage.tsx`、`services/v3/scripts.ts`、`components/script/SceneListEditor.tsx`、测试
- Modify: `router.tsx` — `/projects/:id/editor`（可 `?ep=`）

**UI：**
- 左：集数列表（完成态：有 draft / committed）
- 中：当前集场景列表；每场 heading + 对白/动作文本；自动保存 draft（debounce 1s 可测 fake timers）
- 右：AI「生成本批（如 1–2）」「确认候选」；有 candidate 时 diff 摘要（简单前后字数/集列表即可，不做像素级 diff）
- 无分集计划时禁用生成

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 9: 概览阶段 CTA 与导航打磨

**Files:**
- Modify: `ProjectOverviewPage.tsx`、可选 `DashboardPage` 阶段文案
- Test: overview 测试更新

- [ ] CTA 矩阵：topic→选题；blueprint→蓝图；episodes→分集；writing→编辑器；其后占位「后续开放」

---

### Task 10: W3 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w3-episodes-scripts-acceptance.md`
- Modify: roadmap W3 行

- [ ] **Step 1: 回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api -v 1 --settings=config.settings.sqlite_test

cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/pages/EpisodesPage.test.tsx src/pages/ScriptEditorPage.test.tsx
npm run typecheck
```

- [ ] **Step 2: grep**

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

Expected: 无匹配

- [ ] **Step 3: 勾选验收表；通过后方可写 W4**

---

## Self-Review

| Spec / 验收 | 任务 |
|-------------|------|
| 分集 generate/revise/confirm | Task 2–5, 7 |
| 正文 batch write + confirm | Task 3–4, 6, 8 |
| 草稿与 AI 候选分离 | Task 1, 6, 8 |
| 不引入 Tiptap | Global + Task 8 |
| supersede / 无 v6 | Task 4, 10 |
| 契约命令表 | Task 1 |

无 TBD；`confirm_episode_plan` 为契约新增，须同步 TS。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-23-drama-website-v3-w3-episodes-scripts.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）**
2. **Inline Execution**

Which approach?

# V3 W3 分集 + 正文验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w3-episodes-scripts.md` Task 10  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§4–5 分集/正文）  
> 前置：W2 已通过（`docs/superpowers/baselines/2026-07-23-w2-topic-blueprint-acceptance.md`）  
> 验收日：2026-07-23（Task 10 机跑复核）

## W3 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 蓝图已确认项目可生成分集规划候选并确认；`stage=writing` | `test_v3_episodes_async.py` — `test_generate_and_confirm_episode_plan_advances_to_writing`；`test_v3_episodes_api.py` — generate→confirm→GET committed + stage writing | ☑ |
| 2 | 可对指定集数范围 `revise_episode_plan` 产生新候选（全剧其它集保持） | `test_v3_episodes_async.py` / `test_v3_episodes_api.py` — revise 指定 `episode_numbers` 产出新 candidate；`test_v3_episode_executor.py` 覆盖局部改写 | ☑ |
| 3 | 可对第 1–N 集（N≥1，测试用 1–2）`write_episode_batch` 得到 `episode_scripts` 候选 | `test_v3_episodes_async.py` / `test_v3_scripts_api.py` — write batch → `episode_scripts` (+ `memory_checkpoint`) candidate | ☑ |
| 4 | 可确认脚本候选；正文可在编辑器保存草稿且不覆盖 committed | 后端：`confirm_script_candidate` + `PUT …/draft/`（`test_v3_scripts_api.py`、`test_v3_script_draft.py`）。前端：`ScriptEditorPage` debounce 草稿保存（`ScriptEditorPage.test.tsx` 6 passed） | ☑ |
| 5 | UI：分集看板 + 编辑器；无 operation ID | `EpisodesPage.test.tsx`、`ScriptEditorPage.test.tsx` — `renders Chinese UI without operation recipe ids`；路由 `/projects/:id/episodes`、`/projects/:id/editor` | ☑ |
| 6 | 回归 W0–W2 测试仍绿；新增测全 mock LLM | 后端 **90 tests OK**（含 W0–W2 + W3）；前端 **30 passed** + typecheck exit 0；LLM 经 `V3_LLM_CALL_OVERRIDE` / API mock | ☑ |
| 7 | grep 新代码无 `v6_runtime` / `v6_workbench` / `v6_control_plane` | `rg` 于 `orchestrator/`、`skills_bridge/`、`tasks_v3.py`、`api/v3/` → **0 matches** | ☑ |

## Episodes + Scripts API 路径

前缀：`/api/v3/`（见 `backend/apps/drama/api/v3/urls.py`、`docs/contracts/v3/openapi.yaml`）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/projects/{id}/episodes/` | 分集状态（committed/candidate + 相关 runs） |
| POST | `/projects/{id}/episodes/generate/` | → `generate_episode_plan` |
| POST | `/projects/{id}/episodes/confirm/` | → `confirm_episode_plan` |
| POST | `/projects/{id}/episodes/revise/` | → `revise_episode_plan`（`episode_numbers`） |
| GET | `/projects/{id}/scripts/` | 正文状态（scripts + drafts + runs） |
| POST | `/projects/{id}/scripts/generate/` | → `write_episode_batch`（`episode_range`） |
| POST | `/projects/{id}/scripts/confirm/` | → `confirm_script_candidate`（可选 `use_drafts`） |
| GET | `/projects/{id}/scripts/{episode_number}/` | 单集视图（committed / candidate / draft） |
| GET/PUT | `/projects/{id}/scripts/{episode_number}/draft/` | 人工草稿读写（`V3ScriptDraft`） |

通用：`POST /api/v3/commands/`、`GET /api/v3/commands/{run_id}/` 仍可直接派发上述 command_type。

## W3 确认的命令

| command_type | 模式 | 产物 / 副作用 |
|--------------|------|----------------|
| `generate_episode_plan` | 异步 live | 候选 `episode_plan`（依赖 committed 蓝图） |
| `confirm_episode_plan` | 同步 confirm | candidate→committed；`stage=writing` |
| `revise_episode_plan` | 异步 live | 局部修订 → 新 `episode_plan` candidate |
| `write_episode_batch` | 异步 live | 候选 `episode_scripts` + `memory_checkpoint` |
| `confirm_script_candidate` | 同步 confirm | 脚本候选确认；可 `use_drafts` 合并草稿后 committed；不强制改 stage |

契约源：`docs/contracts/v3/commands.md`；运行时常量：`orchestrator/types.py`（`ASYNC_LIVE_COMMANDS` / `SYNC_CONFIRM_COMMANDS`）。

## 前端路由

| 路由 | 页面 | 备注 |
|------|------|------|
| `/projects/:id` | `ProjectOverviewPage` | CTA：`episodes`→分集、`writing`→编辑器；`quality`/`delivery`→「后续开放」 |
| `/projects/:id/episodes` | `EpisodesPage` | 分集看板：生成 / 确认 / 修订 |
| `/projects/:id/editor` | `ScriptEditorPage` | 结构化场景编辑（`?ep=`）；无 Tiptap |

服务层：`frontend/src/services/v3/episodes.ts`、`scripts.ts`。

## 机跑回归（Task 10 Step 1）

### 后端

```bash
cd backend
# 本地若 DRAMA_SKILLS_ROOT 指向容器路径，需显式设为仓库内 drama-skills
set DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_idempotency -v 1 --settings=config.settings.sqlite_test
```

**结果（2026-07-23）：** `Found 90 test(s)` → **Ran 90 tests in 72.065s — OK**

| 套件 | 覆盖要点 |
|------|----------|
| `test_v3_contract_smoke` … `test_v3_blueprint_api` | W0–W2 回归 |
| `test_v3_script_draft` | `V3ScriptDraft` 模型/唯一约束 |
| `test_v3_episodes_async` | 分集/正文异步主链 + stage |
| `test_v3_episodes_api` | Episodes REST generate/confirm/revise |
| `test_v3_scripts_api` | Scripts REST generate/confirm/draft |
| `test_v3_episode_executor` | recipe/executor 局部修订与写批 |
| `test_v3_idempotency` | 命令幂等 |

### 前端

```bash
cd frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/pages/EpisodesPage.test.tsx src/pages/ScriptEditorPage.test.tsx src/pages/ProjectOverviewPage.test.tsx src/services/v3/scripts.test.ts
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**30 passed**（6 files）— api 2 + router 2 + Episodes 6 + ScriptEditor 6 + Overview 9 + scripts service 5
- typecheck：`tsc -b --pretty false` → exit 0

## grep 验收（Task 10 Step 2）

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

**结果：** 无匹配（0 files）

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| `V3ScriptDraft` | `models.py` + migration `0015_v3_script_draft.py` | ☑ |
| W3 recipes | `skills_bridge/recipe_map.py` — generate/revise/write | ☑ |
| confirm 扩展 | `orchestrator/confirm.py` — `confirm_episode_plan` / `confirm_script_candidate` | ☑ |
| Episodes/Scripts API | `api/v3/episodes_views.py`、`scripts_views.py` | ☑ |
| 前端页 | `EpisodesPage.tsx`、`ScriptEditorPage.tsx` + SceneListEditor | ☑ |
| 契约 | `commands.md` / `openapi.yaml` / `commands.ts` 含 W3 五命令 | ☑ |
| 无 Tiptap | `frontend/package.json` 无编辑器依赖；编辑器为结构化 JSON + textarea | ☑ |

## 已知遗留（不阻塞 W3）

- `frontend/src/studio/**` 与 `api/v2/studio/` 仍保留，W6 再删。
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`（Docker 路径），需覆盖为仓库 `drama-skills` 方可跑测。
- **Tiptap / 富文本编辑器**：明确推迟；W3 用结构化场景列表闭环。
- **UI「用草稿覆盖再确认」**（`use_drafts: true`）：API 已支持，前端未暴露按钮（Task 8 遗留 polish）。
- **质检 / 交付**（`quality` / `delivery`）路由与命令仍为 stub/占位；W4 落地。
- React Router v7 future flag 警告（测试 stderr），不影响本里程碑验收。

## 结论

**全部 W3 验收标准已勾选，机跑回归全绿，grep 无 v6 引用 → W3 视为通过。** 可撰写 W4 实现计划。

验收人：Task 10 agent（机跑复核，未 git commit）

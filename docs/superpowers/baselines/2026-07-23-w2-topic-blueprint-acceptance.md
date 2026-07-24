# V3 W2 选题 + 蓝图验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w2-topic-blueprint.md` Task 9  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§3–5 选题/蓝图）  
> 前置：W1 已通过（`docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md`）  
> 验收日：2026-07-23（Task 9 机跑复核）

## W2 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 对已建项目可触发「生成选题简报」，命令 `queued→running→succeeded`，出现 `project_brief` 候选 | `test_v3_async_commands.py` — `test_generate_topic_brief_eager_succeeds_with_candidate`（eager Celery + mock LLM → succeeded + 1 candidate）。`test_v3_topic_api.py` — `test_generate_get_candidate_confirm_get_committed`（REST generate → GET 见 candidate） | ☑ |
| 2 | 可确认简报；确认后 `stage=blueprint`，存在 `committed` 简报 | `test_v3_async_commands.py` — `test_confirm_topic_brief_commits_and_advances_stage`。`test_v3_topic_api.py` — generate→confirm→GET 见 committed、`stage=blueprint` | ☑ |
| 3 | 可触发「生成蓝图」；五产物均有候选且绑定同一 `command_run` | `test_v3_async_commands.py` — `test_generate_blueprint_with_brief_writes_five_candidates`（5 keys、同一 `command_run_id`）。`test_v3_blueprint_api.py` — `test_generate_get_candidates_confirm_get_committed` | ☑ |
| 4 | 可确认蓝图；`stage=episodes`；五产物 committed | `test_v3_async_commands.py` — `test_confirm_blueprint_advances_to_episodes`。`test_v3_blueprint_api.py` — confirm 后五产物 committed + stage episodes | ☑ |
| 5 | UI：Topic / Blueprint 页无 operation ID；可看到候选人话摘要与确认/重新生成 | `TopicPage.test.tsx` — `renders Chinese UI without operation recipe ids`（6 passed 含 generate/confirm/candidate 交互）。`BlueprintPage.test.tsx` — `renders Chinese tabs without operation recipe ids`（6 passed 含 Tab 与依赖提示） | ☑ |
| 6 | 全套测 LLM 为 mock；W0/W1 回归仍绿 | 后端 47 tests OK（含 W0 smoke、W1 domain/orchestrator/CRUD）；前端 23 tests + typecheck exit 0；async/topic/blueprint 测试均通过 `V3_LLM_CALL_OVERRIDE` 或 API mock 注入 | ☑ |
| 7 | 无 `v6_runtime` / `v6_workbench` / `v6_control_plane` 引用出现在 W2 新增代码路径 | `rg` 于 `orchestrator/`、`skills_bridge/`、`tasks_v3.py`、`api/v3/` → **0 matches**；`test_v3_async_commands.py::test_no_v6_runtime_in_orchestrator_skills_bridge_tasks` 通过 | ☑ |

## 机跑回归（Task 9 Step 1）

### 后端

```bash
cd backend
# 本地若 DRAMA_SKILLS_ROOT 指向容器路径，需显式设为仓库内 drama-skills
set DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api -v 1 --settings=config.settings.sqlite_test
```

**结果（2026-07-23）：** `Found 47 test(s)` → **Ran 47 tests in 35.887s — OK**

| 套件 | 用例数 | 覆盖要点 |
|------|--------|----------|
| `test_v3_contract_smoke` | 3 | W0 list/create projects、billing plans |
| `test_v3_domain_w1` | 2 | `archived_at`、`V3CommandRun` 默认值 |
| `test_v3_orchestrator` | 3 | 同步 create、异步 stub、未知命令 |
| `test_v3_projects_crud` | 6 | CRUD/归档/commands/跨用户 404 |
| `test_v3_artifact` | — | `V3ArtifactVersion` candidate/unique/version |
| `test_v3_skills_bridge` | — | 配方映射、schema 校验、executor mock |
| `test_v3_async_commands` | 6 | generate/confirm 主链、无 v6 引用 |
| `test_v3_topic_api` | 5 | Topic REST generate/draft/confirm |
| `test_v3_blueprint_api` | 4 | Blueprint REST 五产物链 |

### 前端

```bash
cd frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx src/pages/TopicPage.test.tsx src/pages/BlueprintPage.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**23 passed**（6 files）
- typecheck：`tsc -b --pretty false` → exit 0

## grep 验收（Task 9 Step 2）

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

**结果：** 无匹配（0 files）

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| 产物版本模型 | `backend/apps/drama/models.py` — `V3ArtifactVersion`；migration `0014_v3_artifact_version.py` | ☑ |
| Skills 桥 | `backend/apps/drama/skills_bridge/` — `recipe_map.py`、`executor.py`、`validate.py` | ☑ |
| 异步编排 | `orchestrator/async_runner.py`、`confirm.py`、`tasks_v3.py` | ☑ |
| Topic/Blueprint API | `api/v3/topic_views.py`、`blueprint_views.py`、`urls.py` | ☑ |
| 前端页 | `TopicPage.tsx`、`BlueprintPage.tsx`；`services/v3/topic.ts`、`blueprint.ts` | ☑ |
| OpenAPI | `docs/contracts/v3/openapi.yaml` — topic/blueprint paths | ☑ |

## 已知遗留（不阻塞 W2）

- `frontend/src/studio/**` 与 `api/v2/studio/` 仍保留，W6 再删。
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`（Docker 路径），需覆盖为仓库 `drama-skills` 方可跑测；CI 应使用相对路径或 unset 该变量。
- W3+ 命令（分集/正文等）仍为 stub 或待实现。

## 结论

**全部 W2 验收标准已勾选，机跑回归全绿，grep 无 v6 引用 → W2 视为通过。** 可撰写 W3 实现计划。

验收人：Task 9 agent（机跑复核，未 git commit）

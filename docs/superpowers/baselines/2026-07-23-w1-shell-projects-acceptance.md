# V3 W1 编排骨架 + 项目 CRUD + 仪表盘验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w1-shell-projects.md` Task 8  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§9 W1）  
> 前置：W0 已通过（`docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md`）  
> 验收日：2026-07-23（Task 8 机跑复核）

## W1 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 登录用户可在仪表盘看到本人项目列表；可新建（原创/改编）；可进入 `/projects/:id` | `frontend/src/pages/DashboardPage.tsx` — `useQuery` + `listProjects`；`CreateProjectDialog` 支持 `entry_type`；`onSuccess` → `navigate(\`/projects/${project.id}\`)`；卡片 `Link to={/projects/${project.id}}`。`npm test -- src/pages/DashboardPage.test.tsx` → **5 passed**（含列表渲染、对话框提交并跳转） | ☑ |
| 2 | 可归档项目；默认列表不显示已归档；可选「显示已归档」 | 后端 `test_v3_projects_crud.py`：`test_list_excludes_archived_by_default`、`test_archive_hides_from_list_unless_include_archived`。前端 `DashboardPage.tsx` — 归档按钮 + `includeArchived` 开关调用 `listProjects(true)`；`ArchiveConfirmDialog`。`test_v3_projects_crud` + Dashboard 测试绿 | ☑ |
| 3 | `POST /api/v3/commands/` 接受 `create_project`（同步完成并返回 `command_run` + `project`）；未知/异步类型返回明确状态且 **不** 调 LLM | `backend/apps/drama/orchestrator/dispatcher.py` — 同步 `create_project`、异步 `ASYNC_STUB_COMMANDS` → `unsupported`、未知 → `failed`；无 skills/LLM import。`test_v3_orchestrator.py` **3 passed**；`test_v3_projects_crud.py`：`test_commands_create_project_succeeds_with_project`、`test_commands_generate_topic_brief_unsupported` | ☑ |
| 4 | 项目概览展示 `stage`、`entry_type`、下一步文案（选题定调） | `frontend/src/pages/ProjectOverviewPage.tsx` — `ENTRY_LABEL` / `STAGE_LABEL`；主 CTA「去选题定调」→ `/projects/:id/topic`。`frontend/src/app/router.tsx` — `TopicPage` 占位路由 | ☑ |
| 5 | 侧栏导航与 `V3_NAV_PATHS` 单一来源；LoginPage 无 Studio/Operation 黑话 | `router.tsx` — `V3_NAV_ITEMS` → `V3_NAV_PATHS`；`AppShell.tsx` 消费 `V3_NAV_ITEMS`。`LoginPage.tsx` 品牌「ScriptForge / 短剧剧本创作一体机」。`npm test -- src/app/router.test.tsx src/pages/LoginPage.tokens.test.tsx` → **4 passed** | ☑ |
| 6 | W0 冒烟测试仍绿；新增后端/前端测试绿 | 见下方「机跑回归」 | ☑ |

## 机跑回归（Task 8 Step 2）

### 后端

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud -v 1 --settings=config.settings.sqlite_test
```

**结果（2026-07-23）：** `Found 14 test(s)` → **Ran 14 tests in 7.664s — OK**

| 套件 | 用例数 | 覆盖要点 |
|------|--------|----------|
| `test_v3_contract_smoke` | 3 | W0 list/create projects、billing plans |
| `test_v3_domain_w1` | 2 | `archived_at`、`V3CommandRun` 默认值 |
| `test_v3_orchestrator` | 3 | 同步 create、异步 stub、未知命令 |
| `test_v3_projects_crud` | 6 | CRUD/归档/commands/跨用户 404 |

### 前端

```bash
cd frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**11 passed**（4 files）
- typecheck：`tsc -b --pretty false` → exit 0

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| 领域模型 | `backend/apps/drama/models.py` — `V3Project.archived_at`、`V3CommandRun`；migration `0013_v3project_archived_at_v3commandrun.py` | ☑ |
| API 端点 | `backend/apps/drama/api/v3/urls.py` — projects list/create、archive、commands dispatch/detail | ☑ |
| OpenAPI | `docs/contracts/v3/openapi.yaml` — archive、commands paths | ☑ |
| 前端 v3 客户端 | `frontend/src/services/v3/projects.ts` — list/create/get/archive/dispatchCommand | ☑ |
| 编排器包 | `backend/apps/drama/orchestrator/` — `dispatch_command` 公开 API | ☑ |
| 浏览器标题 | `frontend/index.html` — 「ScriptForge · 短剧剧本创作一体机」（Task 8 顺带修正，原 Studio V6） | ☑ |

## 已知遗留（不阻塞 W1）

- `frontend/src/studio/**` 与 `api/v2/studio/` 仍保留，W6 再删（与 roadmap 一致）。
- 异步命令仅登记 `unsupported` 桩，真实 LLM/skills 执行留给 W2+。

## 结论

**全部 W1 验收标准已勾选，机跑回归全绿 → W1 视为通过。** 可撰写 W2 实现计划。

验收人：Task 8 agent（机跑复核，未 git commit）

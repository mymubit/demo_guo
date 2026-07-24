# V3 W5 系统 / 模型 / 日志验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w5-system-models-logs.md` Task 10  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§8 项 4–6）  
> 前置：W4 已通过（`docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md`）  
> 验收日：2026-07-23（Task 10 机跑复核）

## W5 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 可读写系统配置；改 `scoring_preset` / `target_platform` 后 `resolve_system_config()` 返回新值；score/compliance 生成路径读到配置 | `test_v3_system_config`；`test_v3_system_api`；`test_v3_quality_executor` 注入断言 | ☑ |
| 2 | 可 CRUD 供应商（密钥加密、响应无明文）；可 activate；可配置角色映射 | `test_v3_models_api` | ☑ |
| 3 | `test_model_provider`（或 REST test）成功/失败均可记录日志；测试 mock HTTP | `test_v3_provider_test` — CONNECTIVITY_TEST 成功/失败；`@patch(requests.get)` | ☑ |
| 4 | 至少一次 V3 异步生成（mock LLM）后，日志 API 能按 `command_run` 查到对应 call 的 prompt/response | `test_v3_logs_api` — `test_generate_links_llm_call_to_v3_run` | ☑ |
| 5 | UI：`/system` `/models` `/logs` 非占位；无 operation ID；无新依赖 | `SystemPage` / `ModelsPage` / `LogsPage` + 对应 vitest | ☑ |
| 6 | 回归 W0–W4 仍绿；grep 新路径无 v6_runtime | 后端 **178 tests OK**；前端 **19 passed** + typecheck；rg **0 matches** | ☑ |

## System / Models / Logs API 路径

前缀：`/api/v3/`（见 `backend/apps/drama/api/v3/urls.py`）

### System

| Method | Path | 说明 |
|--------|------|------|
| GET | `/system/config/` | 当前生效配置（defaults ⊕ latest overlay） |
| PUT | `/system/config/` | 写入新 `V3SystemConfigRevision` |

### Models

| Method | Path | 说明 |
|--------|------|------|
| GET | `/models/providers/` | 供应商列表（无明文 `api_key`） |
| POST | `/models/providers/` | 创建（密钥加密存储） |
| GET | `/models/providers/{id}/` | 详情（脱敏） |
| PATCH | `/models/providers/{id}/` | 更新 |
| DELETE | `/models/providers/{id}/` | 删除 |
| POST | `/models/providers/{id}/activate/` | 设为 active |
| POST | `/models/providers/{id}/test/` | 试连（mock HTTP；写 CONNECTIVITY_TEST 日志） |
| GET/PUT | `/models/role-mappings/` | 角色 → 模型映射 |

### Logs

| Method | Path | 说明 |
|--------|------|------|
| GET | `/logs/runs/` | 命令运行列表（`project_id` / `status` / `command_type` / 分页） |
| GET | `/logs/runs/{id}/` | run 详情 + 关联 calls 摘要 |
| GET | `/logs/calls/{id}/` | call 全量（含 prompt/response；无 api_key） |

通用：`POST /api/v3/commands/` 可派发 `test_model_provider`（SYNC live）。

## `test_model_provider` + 配置注入 + 日志挂接

| 能力 | 实现要点 | 证据 |
|------|----------|------|
| 试连同步命令 | `SYNC_PROVIDER_TEST_COMMANDS`；dispatcher 同步路由；REST `…/test/` 复用 | `test_v3_provider_test` |
| mock HTTP | `@patch(requests.get)`；无真实外网 | 同上 |
| CONNECTIVITY_TEST 日志 | 成功/失败均写 `llm_call_log`；响应/日志无 `api_key` | 同上 |
| 角色映射覆盖 active | `resolve_for_role` + executor 按 `recipe.role` | 同上 + orch 回归 |
| 系统配置注入 | score/compliance prompt 含 `system_config` / 顶层键 | `test_v3_quality_executor` / `test_v3_system_api` |
| 生成 → call 挂 run | executor `llm_call_scope` 先于 LLM；Logs API 按 run 查 call | `test_v3_logs_api` |

契约源：`docs/contracts/v3/commands.md`（W5 试连约定）；OpenAPI：`/system/**`、`/models/**`、`/logs/**`（含 W4 quality/delivery paths 补洞，Task 1）。

## 前端路由

| 路由 | 页面 | 备注 |
|------|------|------|
| `/system` | `SystemPage` | 读写系统配置；中文 UI；无 operation/recipe ID |
| `/models` | `ModelsPage` | 供应商 CRUD / 激活 / 试连 / 角色映射；密钥不回显明文 |
| `/logs` | `LogsPage` | run 筛选 + 详情 calls + mono prompt/response；可选 JSON 下载 |

服务层：`frontend/src/services/v3/system.ts`、`models.ts`、`logs.ts`。  
侧栏：`router.tsx` NAV — 系统配置 / 模型配置 / 执行日志。

## 机跑回归（Task 10）

### 后端

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_idempotency apps.drama.tests.test_v3_quality_finding apps.drama.tests.test_v3_report_meta apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_executor apps.drama.tests.test_v3_quality_async apps.drama.tests.test_v3_accept_findings apps.drama.tests.test_v3_quality_api apps.drama.tests.test_v3_delivery_api apps.drama.tests.test_v3_system_config apps.drama.tests.test_v3_system_api apps.drama.tests.test_v3_models_api apps.drama.tests.test_v3_provider_test apps.drama.tests.test_v3_logs_api -v 1 --settings=config.settings.sqlite_test
```

**结果（2026-07-23）：** `Found 178 test(s)` → **Ran 178 tests in 137.506s — OK**

| 套件 | 覆盖要点 |
|------|----------|
| `test_v3_contract_smoke` … `test_v3_delivery_api` | W0–W4 回归 |
| `test_v3_system_config` / `test_v3_system_api` | resolver + System REST + 注入 |
| `test_v3_models_api` | Provider CRUD / activate / role-mappings |
| `test_v3_provider_test` | 试连 live + CONNECTIVITY_TEST |
| `test_v3_logs_api` | Logs REST + generate→call 挂接 |

### 前端

```bash
cd frontend
npm test -- src/pages/SystemPage.test.tsx src/pages/ModelsPage.test.tsx src/pages/LogsPage.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**19 passed**（3 files）— System 5 + Models 8 + Logs 6
- typecheck：`tsc -b --pretty false` → exit 0

## grep 验收

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3 backend/apps/drama/tasks_v3.py
```

**结果：** 无匹配（0 files）

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| `V3SystemConfigRevision` + resolver | `models.py` + `orchestrator/system_config.py` | ☑ |
| System REST | `api/v3/system_views.py` | ☑ |
| Provider / RoleMapping REST | `api/v3/models_views.py` | ☑ |
| 试连 | `orchestrator/provider_test.py` + SYNC 命令 | ☑ |
| LLM 日志 v3 FK + Logs API | migration + `llm_call_log_service` + `logs_views.py` | ☑ |
| 前端三页 | `SystemPage` / `ModelsPage` / `LogsPage` | ☑ |
| OpenAPI W4+W5 paths | Task 1 已补 quality/delivery/system/models/logs | ☑ |
| 无真实外网试连 / 无新依赖 | mock HTTP；package 无新增库 | ☑ |

## 已知遗留（不阻塞 W5；部分已在后续里程碑 / polish 关闭）

- ~~**试连日志未挂 `v3_command_run`**~~：**已关闭（W5 终审 Important 修复）** — `provider_test` 经 `llm_call_scope` 挂 run；见 `test_v3_provider_test`。
- ~~**OpenAPI 日期筛选参数**~~：**已关闭** — `listLogRuns` 契约已列 `created_after` / `created_before`。
- **OpenAPI `additionalProperties: false` vs 实现 warn+忽略未知键**：REST/契约严格；resolver 宽松，前端按 schema 无冲突。
- ~~**`prepare_delivery` 未注入 system_config**~~：**已关闭** — `_SYSTEM_CONFIG_COMMANDS` 含 `prepare_delivery`。
- ~~**LogsPage 分页**~~：**已关闭** — 上一页/下一页 + offset。
- **刻意不做**：多 Key 轮询、自动 failover、成本预估图、ECharts 链路图、按 owner 隔离的系统配置、真实外网试连。
- ~~`frontend/src/studio/**` 与 `api/v2/studio/`~~：**已关闭（W6）**。
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库 `drama-skills` 方可跑测。
- React Router v7 future flag 警告（测试 stderr），不影响本里程碑验收。

## 结论

**全部 W5 验收标准已勾选，机跑回归全绿，grep 无 v6 引用 → W5 视为通过。** 可撰写并执行 W6 实现计划。

验收人：Task 10 agent（机跑复核，未 git commit）

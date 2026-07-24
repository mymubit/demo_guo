# V3 W4 质检 + 交付验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-w4-quality-delivery.md` Task 10  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§4–5 质检/交付，§8 项 2–3）  
> 前置：W3 已通过（`docs/superpowers/baselines/2026-07-23-w3-episodes-scripts-acceptance.md`）  
> 验收日：2026-07-23（Task 10 机跑复核）

## W4 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 有 committed 正文时可触发质量评分与合规审查；报告 committed；`stage` 可进 `quality` | `test_v3_quality_async` / `test_v3_quality_api` — score/compliance → committed 报告；writing→quality | ☑ |
| 2 | 报告带 `source_script_version`；正文升版后 GET `is_stale=true`；过期报告不可用于门禁通过 | `test_v3_report_meta`；`test_v3_delivery_gate` stale 阻断；API GET `quality_is_stale` / `compliance_is_stale` | ☑ |
| 3 | 可 `accept_findings` 接受指定问题；列表可查 | `test_v3_accept_findings`；`test_v3_quality_api` accept + GET findings | ☑ |
| 4 | 可 `revise_from_findings` 得到脚本候选；确认后旧报告过期 | `test_v3_quality_async` / `test_v3_quality_api` revise → candidate；confirm 后 stale | ☑ |
| 5 | 双报告未通过 / 过期时 `prepare_delivery` 失败并说明原因；通过后 `production_package` committed，`stage=delivery` | `test_v3_delivery_gate`、`test_v3_quality_async`、`test_v3_delivery_api` | ☑ |
| 6 | UI：`/projects/:id/quality`、`/delivery`；概览 CTA 接通；无 operation ID；无新依赖 | `QualityPage` / `DeliveryPage` / Overview CTA；导出 JSON+MD；无 Word/PDF/ECharts | ☑ |
| 7 | 回归 W0–W3 仍绿；grep 新路径无 v6_runtime | 后端 **143 tests OK**；前端 **24 passed** + typecheck；rg **0 matches** | ☑ |

## Quality + Delivery API 路径

前缀：`/api/v3/`（见 `backend/apps/drama/api/v3/urls.py`）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/projects/{id}/quality/` | 双报告 + findings + `*_is_stale` + latest runs |
| POST | `/projects/{id}/quality/score/` | → `score_quality` |
| POST | `/projects/{id}/quality/compliance/` | → `check_compliance` |
| POST | `/projects/{id}/quality/accept/` | → `accept_findings` |
| POST | `/projects/{id}/quality/revise/` | → `revise_from_findings` |
| GET | `/projects/{id}/delivery/` | gate 快照 + package（若有）+ latest_run |
| POST | `/projects/{id}/delivery/prepare/` | → `prepare_delivery` |

通用：`POST /api/v3/commands/`、`GET /api/v3/commands/{run_id}/` 仍可直接派发上述 command_type。

> **OpenAPI：** W5 Task 1 已补登记 `/projects/{id}/quality/**`、`/delivery/**` paths（见现行 `openapi.yaml`）。本基线撰写时曾记为缺口，现已关闭。

## W4 确认的命令

| command_type | 模式 | 产物 / 副作用 |
|--------------|------|----------------|
| `score_quality` | 异步 live | `quality_report` 直接 **committed**（supersede）；writing→quality |
| `check_compliance` | 异步 live | `compliance_report` 直接 **committed**；writing→quality |
| `accept_findings` | 同步 mutation | upsert `V3QualityFinding(status=accepted)`；无 LLM |
| `revise_from_findings` | 异步 live | `episode_scripts` + `memory_checkpoint` **candidate**；确认用 `confirm_script_candidate` |
| `prepare_delivery` | 异步 live | 门禁通过后 `production_package` **committed**；`stage=delivery` |

契约源：`docs/contracts/v3/commands.md`；运行时常量：`orchestrator/types.py`。

## Staleness + 门禁规则摘要

### 报告过期（staleness）

- 生成质量/合规报告时写入 `_v3_meta.source_script_version`（及 artifact id）。
- `is_stale = true` 当且仅当：当前 committed `episode_scripts.version` ≠ `source_script_version`。
- 正文经 `confirm_script_candidate`（含 `use_drafts`）升版后，旧报告自动过期；过期报告不可使门禁通过。

### 交付门禁（`delivery_gate.evaluate`，无 LLM）

1. 存在 committed `episode_scripts`，否则阻断「请先确认正文」
2. 存在 **未过期** committed `quality_report`，且 `verdict in ("通过","条件通过")` **或**（`grade in ("S","A","B")` 且 `needs_revision is False`）
3. 存在 **未过期** committed `compliance_report`，且 `overall_result == "通过"`
4. `compliance_report.blocking_issues` 中未 `accepted` 的项 → 阻断（空则跳过）
5. 全部通过 → `passed=True`

`prepare_delivery` 在入队 LLM 前同步跑门禁；失败则 run=`failed`，`error_message` 为人话拼接 blockers。

## 前端路由

| 路由 | 页面 | 备注 |
|------|------|------|
| `/projects/:id` | `ProjectOverviewPage` | CTA：`quality`→质检中心、`delivery`→交付中心 |
| `/projects/:id/quality` | `QualityPage` | 评分 / 合规 / 接受问题 / 按问题修订；十维 CSS 条 |
| `/projects/:id/delivery` | `DeliveryPage` | gate blockers；打包；下载 JSON + Markdown |

服务层：`frontend/src/services/v3/quality.ts`、`delivery.ts`。

## 机跑回归（Task 10）

### 后端

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_idempotency apps.drama.tests.test_v3_quality_finding apps.drama.tests.test_v3_report_meta apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_executor apps.drama.tests.test_v3_quality_async apps.drama.tests.test_v3_accept_findings apps.drama.tests.test_v3_quality_api apps.drama.tests.test_v3_delivery_api -v 1 --settings=config.settings.sqlite_test
```

**结果（2026-07-23）：** `Found 143 test(s)` → **Ran 143 tests in 62.561s — OK**

| 套件 | 覆盖要点 |
|------|----------|
| `test_v3_contract_smoke` … `test_v3_idempotency` | W0–W3 回归 |
| `test_v3_quality_finding` / `test_v3_report_meta` | Finding 模型 + 过期 meta |
| `test_v3_delivery_gate` / `test_v3_quality_executor` | 门禁 + direct-commit |
| `test_v3_quality_async` / `test_v3_accept_findings` | 编排 live + accept |
| `test_v3_quality_api` / `test_v3_delivery_api` | Quality/Delivery REST |

### 前端

```bash
cd frontend
npm test -- src/pages/QualityPage.test.tsx src/pages/DeliveryPage.test.tsx src/pages/ProjectOverviewPage.test.tsx src/services/v3/delivery.test.ts
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**24 passed**（4 files）— Quality 8 + Delivery 5 + Overview 9 + delivery service 2
- typecheck：`tsc -b --pretty false` → exit 0

## grep 验收

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

**结果：** 无匹配（0 files）

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| `V3QualityFinding` | `models.py` + migration `0016_v3_quality_finding.py` | ☑ |
| `delivery_gate` / `report_meta` | `orchestrator/delivery_gate.py`、`report_meta.py` | ☑ |
| W4 recipes | `skills_bridge/recipe_map.py` — score/compliance/revise/prepare | ☑ |
| Quality/Delivery API | `api/v3/quality_views.py`、`delivery_views.py` | ☑ |
| 前端页 | `QualityPage.tsx`、`DeliveryPage.tsx` + DimensionBars | ☑ |
| 契约命令表 | `commands.md` 含 W4 五命令；`accept_findings` 同步说明 | ☑ |
| 无 Word/PDF/ECharts | 导出 JSON+MD；十维 CSS 条；无新依赖 | ☑ |

## 已知遗留（不阻塞 W4）

- **OpenAPI paths**：`QualityState`/`DeliveryState` schema 已有，但 `/projects/{id}/quality/**`、`/delivery/**` 路径未写入 `openapi.yaml` paths。
- **Word / PDF 导出**：明确推迟；W4 仅浏览器下载 `production_package.json` + `delivery.md`。
- **ECharts / 雷达图**：不做；十维用 CSS 条形。
- **一键双检**：评分与合规为两个按钮，未做并行单按钮。
- **像素级剧本定位跳转**：不做。
- ~~`frontend/src/studio/**` 与 `api/v2/studio/`~~：**已关闭（W6）**。
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库 `drama-skills` 方可跑测。
- React Router v7 future flag 警告（测试 stderr），不影响本里程碑验收。
- `OverviewStageCta.placeholder` 联合类型仍保留，六阶段均已返回 `link`。

## 结论

**全部 W4 验收标准已勾选，机跑回归全绿，grep 无 v6 引用 → W4 视为通过。** 可撰写并执行 W5 实现计划。

验收人：Task 10 agent（机跑复核，未 git commit）

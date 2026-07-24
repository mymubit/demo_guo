# V3 W0 契约冻结验收清单（2026-07-22）

> 计划：`docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md` Task 6  
> 设计：`docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`  
> 验收日：2026-07-23（Task 6 工作树复核）

## 机跑验收项

| 项 | 证据 | 结果 |
|----|------|------|
| glossary + commands 存在 | `docs/contracts/v3/glossary.md`（8 行术语映射 + 使用说明）；`docs/contracts/v3/commands.md`（15 条 `command_type` + Spec §5 模块对照） | ☑ |
| openapi.yaml 含 projects/billing | `docs/contracts/v3/openapi.yaml` — paths: `/projects/`、`/projects/{project_id}/`、`/billing/plans/`；含 `Envelope` / `ProjectSummary` / `BillingPlan` schemas | ☑ |
| TS 命令枚举测试绿 | `cd frontend && npm test -- src/types/v3/api.test.ts` → **1 passed**；`PRODUCT_COMMAND_TYPES` 含 15 条 snake_case，不含 `create-project-brief` | ☑ |
| test_v3_contract_smoke 绿 | `cd backend && py -3 manage.py test apps.drama.tests.test_v3_contract_smoke -v 2 --settings=config.settings.sqlite_test` → **Ran 3 tests … OK**（list/create projects、billing plans ≥3 档） | ☑ |
| 前端无 /studio 路由 | `frontend/src/App.tsx` 仅挂 `V3Routes`，零 studio import；`frontend/src/app/router.tsx` 无 `/studio` path；`npm test -- src/app/router.test.tsx` → **1 passed**（`V3_NAV_PATHS` 不含 `/studio` 前缀） | ☑ |
| 创作者文案无 operation.* | 占位页抽查：`DashboardPage`、`ModelsPage`、`LogsPage`、`SystemPage`、`BillingPage`、`ProjectOverviewPage` — 均为中文业务标题，无 `operation.*` / skills 配方 ID / `OperationRun` | ☑ |

## 附加复核（非阻塞，Task 5 延续）

| 项 | 证据 | 结果 |
|----|------|------|
| 前端 typecheck | `cd frontend && npm run typecheck` → exit 0 | ☑ |
| 后端 v3 路由挂载 | `backend/config/urls.py` → `path("api/v3/", include("apps.drama.api.v3.urls"))` | ☑ |
| v2 studio 保留（W6 再删） | `backend/config/urls.py` 仍含 `api/v2/studio/` include | ☑ |

## 已知遗留（不阻塞 W0）

- `frontend/src/pages/LoginPage.tsx` 侧栏仍含英文品牌文案（如「Studio V6」「Operation graph …」）；登录后已跳转 `/dashboard`，不在 W0 占位页验收范围内。建议 W1 统一为 V3 产品中文。

## 结论

**全部机跑验收项已勾选 → W0 契约冻结视为通过。** 可进入 W1 实现计划撰写。

验收人：Task 6 agent（工作树复核，未 git commit）

# P2-W2 主备 UI + 单价 + rollup + Usage API 验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p2-w2-prices-usage-api.md` Task 6  
> Roadmap：`docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`  
> Spec：`docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`（§4.3–4.4、§6、§7）  
> 前置：P2-W1 已通过（`docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md`）  
> 验收日：2026-07-23（Task 6 机跑复核）

## P2-W2 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 单价 CRUD：`V3ModelPrice` + `GET/PUT /api/v3/models/prices/` | `test_v3_model_price`；`test_v3_prices_api` | ☑ |
| 2 | 日 rollup 增量；无单价时 `unpriced_call_count` 累加；Asia/Shanghai 日 | `test_v3_usage_rollup` | ☑ |
| 3 | Usage summary：owner 隔离；`group_by`；`live=0/1`；含 `unpriced_call_count` | `test_v3_usage_api` | ☑ |
| 4 | Models 主备 UI：主供应商 + 有序备选；PUT `backup_provider_ids` | `ModelsPage.test.tsx`；`test_v3_models_api` role-mappings | ☑ |
| 5 | 无 ECharts / 无 `UsagePage`（属 P2-W3） | 手检 `package.json` + 路径 | ☑ |

## Prices / Usage / Models API 路径

前缀：`/api/v3/`（见 `backend/apps/drama/api/v3/urls.py`）

### Prices

| Method | Path | 说明 |
|--------|------|------|
| GET | `/models/prices/` | 单价列表 |
| PUT | `/models/prices/` | 全量 upsert（`provider_id` + `model_name`） |

### Usage

| Method | Path | 说明 |
|--------|------|------|
| GET | `/usage/summary/` | 查询参数：`project_id`、`date_from`、`date_to`、`group_by=day\|model\|command_type`、`live=0\|1`；`timezone` 固定 `Asia/Shanghai` |

### Models（本里程碑相关）

| Method | Path | 说明 |
|--------|------|------|
| GET/PUT | `/models/role-mappings/` | 含 `backup_provider_ids` 有序备选链 |

契约：`docs/contracts/v3/openapi.yaml`；前端：`services/v3/prices.ts`、`usage.ts`、`models.ts`。

## 机跑回归（Task 6）

### 后端

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_model_price apps.drama.tests.test_v3_usage_rollup apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_models_api --settings=config.settings.sqlite_test -v 1
```

**结果（2026-07-23）：** `Found 38 test(s)` → **Ran 38 tests in 16.756s — OK**（exit 0）

| 套件 | 用例数 | 覆盖要点 |
|------|--------|----------|
| `test_v3_model_price` | 2 | `V3ModelPrice` 创建 / unique |
| `test_v3_usage_rollup` | 7 | priced/unpriced 增量、同日 upsert、Shanghai 日 |
| `test_v3_prices_api` | 7 | GET/PUT CRUD、校验、鉴权 |
| `test_v3_usage_api` | 12 | summary owner 隔离、`group_by`、`live` 无双计 |
| `test_v3_models_api` | 10 | Provider / role-mappings（含备选链）回归 |

### 前端

```bash
cd frontend
npm test -- --run src/pages/ModelsPage.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**10 passed**（1 file）— 含主备添加/排序/删除与 PUT `backup_provider_ids`
- typecheck：`tsc -b --pretty false` → exit 0

## 手检：无 ECharts / UsagePage

```powershell
Test-Path frontend\src\pages\UsagePage.tsx   # False
Select-String -Path frontend\package.json -Pattern echarts   # 无匹配
rg -n "echarts|ECharts|UsagePage" frontend/src frontend/package.json   # 0 hits
```

**结果：** 无 `UsagePage.tsx`；`package.json` 无 `echarts` 依赖；源码无 ECharts/UsagePage 引用。

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| `V3ModelPrice` + migration `0021` | `models.py` + `test_v3_model_price` | ☑ |
| `V3UsageDailyRollup` + migration `0022` | `models.py` + `orchestrator/usage_rollup.py` | ☑ |
| call log → rollup 挂接 | `llm_call_log_service` + rollup tests | ☑ |
| Prices REST | `api/v3/prices_views.py` | ☑ |
| Usage summary REST | `api/v3/usage_views.py` | ☑ |
| ModelsPage 主备编辑 | `ModelsPage.tsx` + vitest | ☑ |
| 无新第三方库 / 无 ECharts | `package.json` 手检 | ☑ |

## 已知遗留（不阻塞 P2-W2；属后续里程碑）

- **`/usage` 页面 + ECharts 图表**：P2-W3（本里程碑刻意不加图表库与 UsagePage）
- SQLite 警告：`V3UsageDailyRollup` unique nulls distinct（models.W047）— 测试库提示，不阻塞验收
- React Router v7 future flag 警告（测试 stderr），不影响验收
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库 `drama-skills` 方可跑测

## 结论

**全部 P2-W2 验收标准已勾选，机跑全绿（后端 38 + 前端 10 + typecheck），无 ECharts/UsagePage → P2-W2 视为通过。** 可撰写并执行 P2-W3。

验收人：Task 6 agent（机跑复核，未 git commit）

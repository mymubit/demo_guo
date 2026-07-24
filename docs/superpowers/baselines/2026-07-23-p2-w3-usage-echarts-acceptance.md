# P2-W3 `/usage` + ECharts + 全量回归验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p2-w3-usage-echarts.md` Task 3  
> Roadmap：`docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`  
> Spec：`docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`（§7、§8.2）  
> 前置：P2-W1 / P2-W2 已通过  
> 验收日：2026-07-23（Task 3 机跑复核）

## Spec §8.2 项 3（本里程碑主验收）

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 3 | `/usage` 按筛选可见 token 与估算费用（含 ECharts） | `UsagePage` + `UsagePage.test.tsx`（筛选/表/图表容器/`未定价`）；路由 `/usage`；`echarts@5.5.1`；`GET /api/v3/usage/summary/`（`test_v3_usage_api`，含 live 无双计） | ☑ |

## Phase-2 收口清单（Spec §8.2 全项）

| # | 标准 | 证据（里程碑） | 结果 |
|---|------|----------------|------|
| 1 | 主挂备通：同 run ≥2 attempt，产物成功 | P2-W1：`test_v3_failover_executor` / `test_v3_llm_router` | ☑ |
| 2 | 链耗尽：run 失败且 attempt 全记录 | P2-W1：`test_v3_llm_router.test_exhausted_chain_raises_with_zh_summary` | ☑ |
| 3 | `/usage` 按筛选可见 token/费用 + ECharts | 本基线 §上表 + 机跑 | ☑ |
| 4 | 无支付/配额；无 Tiptap；legacy v2/v6 产品路径仍净 | 约束手检；`test_v3_legacy_gone`（本机跑） | ☑ |
| 5 | 试连不误走备选链 | P2-W1：`test_v3_failover_executor.test_connectivity_does_not_create_failover_attempts`；本机跑含 failover executor | ☑ |

## 前端交付抽查

| 项 | 证据 | 结果 |
|----|------|------|
| 路由 `/usage` | `router.tsx` — `path="/usage"`；nav「用量」/ hint「Token 与费用」；位于 Logs 与 System 之间 | ☑ |
| `UsagePage` | 筛选（项目/日期/`group_by`）+ 汇总表 + 趋势图/按模型对比图容器 | ☑ |
| ECharts 钉版本 | `frontend/package.json` → `"echarts": "5.5.1"`；Usage 动态 import | ☑ |
| 未定价展示 | `estimated_cost=null` →「未定价」；`UsagePage.test.tsx` | ☑ |
| 默认 `live=0` | 页面请求默认 rollup；无双计由 API 测覆盖 | ☑ |
| 无 operation ID | Usage/Models vitest 中文 UI 断言 | ☑ |

## 机跑回归（Task 3）

### 后端

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_legacy_gone --settings=config.settings.sqlite_test -v 1
```

**结果（2026-07-23）：** `Found 26 test(s)` → **Ran 26 tests in 12.385s — OK**（exit 0）

| 套件 | 覆盖要点 |
|------|----------|
| `test_v3_usage_api` | summary 筛选/`group_by`/`live`；**live 无双计**；`unpriced_call_count` |
| `test_v3_prices_api` | 单价 GET/PUT 回归 |
| `test_v3_failover_executor` | 主挂备通写 attempt；试连不走备选 |
| `test_v3_legacy_gone` | v2/studio Gone；legacy 路径净 |

### 前端

```bash
cd frontend
npm test -- --run src/pages/UsagePage.test.tsx src/pages/ModelsPage.test.tsx src/app/router.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**18 passed**（3 files）— Usage 5 + Models 10 + router 3
- typecheck：`tsc -b --pretty false` → exit 0

## 手检

| 项 | 命令/观察 | 结果 |
|----|-----------|------|
| echarts 5.5.1 | `package.json` `"echarts": "5.5.1"` | ☑ |
| `/usage` 路由存在 | `router.tsx` + `router.test.tsx` | ☑ |
| 无支付/配额/Tiptap 引入 | phase-2 Global Constraints；本里程碑仅加 echarts | ☑ |

## 已知遗留（不阻塞 phase-2）

- SQLite 警告：`V3UsageDailyRollup` unique nulls distinct（models.W047）— 测试库提示
- React Router v7 future flag 警告（测试 stderr），不影响验收
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库 `drama-skills` 方可跑测
- 刻意不做：支付/配额、Tiptap、真实外网 LLM

## 结论

**Spec §8.2 项 3 已勾选；phase-2 §8.2 五项全绿；机跑后端 26 + 前端 18 + typecheck 通过；echarts@5.5.1 与 `/usage` 已落地 → P2-W3 通过，V3 Phase-2（Failover + 用量可观测）视为完成。**

验收人：Task 3 agent（机跑复核，未 git commit）

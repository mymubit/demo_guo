# P2-W3 Task 1 Review — echarts + UsagePage

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `frontend/package.json` / lock；`UsagePage.tsx`；`UsagePage.test.tsx`；`loadEcharts.ts`  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `echarts@5.5.1` in `package.json` + lock | ✅ `"echarts": "5.5.1"`；lock `node_modules/echarts` → `5.5.1` |
| 筛选：项目 / date_from / date_to / group_by（day\|model） | ✅ 四个控件 + `getUsageSummary` 传参 |
| 汇总表 rows + totals（token、estimated_cost、unpriced_call_count） | ✅ `MetricsCells` + 合计行 |
| `estimated_cost` null/空 →「未定价」 | ✅ `formatEstimatedCost` + 专用测试 |
| ECharts：按日折线/柱（token + 费用）；按模型柱图 | ✅ `buildTrendOption` / `buildByModelOption` |
| 动态 `import('echarts')` | ✅ `loadEcharts.ts` → `import('echarts')`；`ChartHost` 经 `loadEcharts()` 加载 |
| 图表容器 `data-testid` | ✅ `usage-chart-trend` / `usage-chart-by-model` |
| 默认 `live=0` | ✅ `baseFilters.live: 0 as const`；测试断言全部调用 |
| 中文标题「用量」 | ✅ `PageShell title="用量"`；测试 `findByRole('heading', { name: '用量' })` |
| 无 operation ID 展示 | ✅ 页面无 operation 字段；测试 `queryByText(/operation\./i)` 为 null |
| TDD：标题、筛选、表、图表容器 | ✅ 5 cases；独立复跑 **5 passed** |
| `npm run typecheck` | ✅ OK |

**Notes:** 任务 brief 未要求注册应用路由；`UsagePage` 仅在测试中挂载 `/usage`，属预期范围外，不计入 Spec 缺口。

---

## Code quality: Approved

实现与项目既有模式一致（`PageShell`、`useQuery`、`formatApiError`、中文 UI）。`loadEcharts` 抽离便于 mock，符合 brief「动态 import + 可测」意图。表格与双图表数据分离（三 query）合理：表格随 `groupBy` 切换，图表固定 day/model 维度。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor
1. **图表加载失败静默** — `ChartHost` 中 `loadEcharts().catch(() => {})` 无用户提示；生产环境 echarts chunk 失败时页面仅空白图表区（可接受于 Task 1，后续可加 toast）。
2. **动态 import 未在测试中断言调用** — mock 了 `loadEcharts`，但未 `expect(loadEcharts).toHaveBeenCalled()`；实现正确，测试未完全锁定 lazy-load 行为。
3. **首屏三并发 summary 请求** — 表格 + 趋势 + 按模型各一次 `getUsageSummary`；符合双图独立数据需求，后续若 API 支持可合并为单次响应。

---

## Strengths

- `echarts` 版本钉死 `5.5.1`，lock 一致。
- 「未定价」、中文「用量」、`live=0`、testid 均实现且有用例覆盖。
- `resolveEchartsModule` 兼容 default/named export，健壮。
- `ChartHost` cleanup（`disposed` + `dispose`）与 jsdom 容错处理得当。
- TDD 证据可信；独立复跑测试与 typecheck 均通过。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 3 |

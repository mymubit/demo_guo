# P2-W3 Task 1 Report — echarts + UsagePage

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** 安装 `echarts@5.5.1`；新建 `UsagePage`（筛选 + 汇总表 + 动态 ECharts）

---

## Deliverables

| File | Action |
|------|--------|
| `frontend/package.json` / lock | Modified — `echarts` 钉版本 `5.5.1` |
| `frontend/src/pages/UsagePage.tsx` | Created — PageShell、筛选、表、双图表 |
| `frontend/src/pages/UsagePage.test.tsx` | Created — TDD（5 cases） |
| `frontend/src/utils/loadEcharts.ts` | Created — `import('echarts')` 包装，便于测试 mock |

---

## TDD Evidence

### RED
`npm test -- --run src/pages/UsagePage.test.tsx` → `Failed to resolve import "./UsagePage"`

### GREEN
同命令 → **5 passed**；`npm run typecheck` → OK

---

## Self-Review

| Check | Result |
|-------|--------|
| 默认 `live=0` | ✓ |
| 筛选 project / date_from / date_to / group_by day\|model | ✓ |
| 表 rows + totals；`estimated_cost` null →「未定价」 | ✓ |
| `usage-chart-trend` / `usage-chart-by-model` | ✓ |
| 中文「用量」；无 operation ID | ✓ |
| 动态 `import('echarts')`（经 `loadEcharts`） | ✓ |

**Commit:** 跳过（按任务要求）

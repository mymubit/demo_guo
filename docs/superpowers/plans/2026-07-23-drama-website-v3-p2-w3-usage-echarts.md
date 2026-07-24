# V3 P2-W3 `/usage` + ECharts + 全量回归 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`. Continuous execution — no human confirmation between tasks. Checkbox tracking.

**Goal:** 新建 `/usage` 页：筛选 + 汇总表 + ECharts（按日 token/费用趋势、按模型对比）；全量回归勾选 Spec §8.2 项 3；更新 phase-2 roadmap 收口。

**Architecture:** 复用 `GET /api/v3/usage/summary/`（默认 live=0）；ECharts 仅 Usage 页动态 import。

**Tech Stack:** React + TanStack Query；**echarts@5.5.1**（钉版本；理由：产品需要趋势/对比图，K3 决策；仅 Usage 动态 import 控制体积）。

**Spec:** phase-2 design §7 UsagePage、§8.2 项 3  
**Prerequisite:** P2-W2 ✅

## Global Constraints

- 无支付/配额/Tiptap
- 禁止 v2/v6 加功能；UI 无 operation ID
- ECharts 仅 Usage 动态 import；版本 **5.5.1**
- Commit 跳过
- 工作目录 `c:\Users\99193\Desktop\demo_guo`

## File Map

| 职责 | 路径 |
|------|------|
| 依赖 | `frontend/package.json` echarts@5.5.1 |
| 页面 | `frontend/src/pages/UsagePage.tsx` + test |
| 路由 | `frontend/src/app/router.tsx` |
| 服务 | 已有 `services/v3/usage.ts` |
| 基线 | `docs/superpowers/baselines/2026-07-23-p2-w3-usage-echarts-acceptance.md` |

---

### Task 1: 安装 echarts + UsagePage

**Files:** package.json；Create UsagePage.tsx；Create UsagePage.test.tsx

**UI:**
- 筛选：项目、date_from、date_to、group_by（day/model）
- 汇总表：rows + totals（token、estimated_cost、unpriced_call_count；未定价显示「未定价」）
- ECharts：折线/柱状按日 token 与费用；按模型对比柱图
- 动态 `import('echarts')`；中文；无 operation ID
- 默认 `live=0`

- [ ] TDD：渲染标题「用量」、筛选、表、图表容器 data-testid
- [ ] npm install echarts@5.5.1
- [ ] Implement
- [ ] Commit 跳过

---

### Task 2: 路由与导航

**Files:** `router.tsx` + router.test if any

- 路径 `/usage`，nav：「用量」，hint：「Token 与费用」；放在 Logs 与 System 之间
- 测试路由可访问

- [ ] Implement + test
- [ ] Commit 跳过

---

### Task 3: 全量回归 + 基线

机跑：
```powershell
# backend focused P2 + legacy
py -3 manage.py test apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_legacy_gone --settings=config.settings.sqlite_test -v 1
```
```bash
cd frontend && npm test -- --run src/pages/UsagePage.test.tsx src/pages/ModelsPage.test.tsx src/app/router.test.tsx && npm run typecheck
```

验收：`/usage` 可见 token/费用图；无双计；Spec §8.2 项 3；roadmap P2-W3 ✅ phase-2 complete.

- [x] 写基线 + 更新 roadmap
- [x] Commit 跳过

---

## Spec coverage

| Spec | Task |
|------|------|
| §7 /usage + ECharts | T1–T2 |
| §8.2 项 3 | T3 |
| phase-2 收口 | T3 |

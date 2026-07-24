# V3 Phase-2 Roadmap：Failover + 用量可观测

> **For agentic workers:** 按里程碑拆分执行。**Spec 已确认。** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`。

**Goal:** 跨供应商主备 failover + `/usage` token/费用可观测（ECharts）。

**Spec:** `docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`

**Architecture:** 方案 2 — `failover_policy` + `LlmRouter` + `V3FailoverAttempt` + 日 rollup；新建 `/usage`；Models 扩展备选链。

## Global Constraints

- 不引入 Tiptap / 支付 / 配额
- 禁止往 `v2_*` / `v6_runtime` / `v6_workbench` / `v6_control_plane` 加功能
- UI 不暴露 operation/recipe ID
- 测试 mock LLM；禁止真实外网
- ECharts **仅 P2-W3** 引入（钉版本）；W1/W2 不加图表库
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`；`DRAMA_SKILLS_ROOT` → 仓库 `drama-skills`

## Milestone Index

| 里程碑 | Plan | 状态 |
|--------|------|------|
| **P2-W1** Failover 运行时 + Logs 尝试 | `2026-07-23-drama-website-v3-p2-w1-failover-runtime.md` | ✅ 通过 — 基线 `docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md` |
| **P2-W2** 主备 UI + 单价 + rollup + Usage API | `2026-07-23-drama-website-v3-p2-w2-prices-usage-api.md` | ✅ 通过 — 基线 `docs/superpowers/baselines/2026-07-23-p2-w2-prices-usage-api-acceptance.md` |
| **P2-W3** `/usage` + ECharts + 全量回归 | `2026-07-23-drama-website-v3-p2-w3-usage-echarts.md` | ✅ 通过 — 基线 `docs/superpowers/baselines/2026-07-23-p2-w3-usage-echarts-acceptance.md` |

## Execution Order

1. 完成并验收 **P2-W1**
2. 撰写并执行 **P2-W2**
3. 撰写并执行 **P2-W3**（Spec §8 验收全绿）

## Phase-2 Status

**Phase-2 complete（2026-07-23）。** Spec §8.2 五项已全勾选；交付物：跨供应商主备 failover + `/usage` token/费用可观测（ECharts 5.5.1）。详见 P2-W1/W2/W3 基线。

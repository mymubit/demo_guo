# V3 P3-W4 日费用预警 + 全量回归 Implementation Plan

> Continuous SDD; no human gate.

**Goal:** system overlay `daily_cost_alert_cny` + Usage/Dashboard 横幅 + Usage 行着色；phase-3 全量回归基线。

## Tasks

### Task 1: system overlay 新键

- ALLOWED_OVERLAY_KEYS += `daily_cost_alert_cny`
- sanitize: null/number >= 0；effective 带回
- OpenAPI + SystemPage 输入框「日费用预警阈值（元）」
- Tests extend test_v3_system_*

### Task 2: Usage + Dashboard 横幅与着色

- UsagePage: fetch today's cost via usage summary; if threshold set and cost > threshold show banner
- Color rows when estimated_cost high relative to threshold (e.g. day group_by and key=today)
- DashboardPage: same banner if over
- LogsPage optional: light tint if run created today and global over — keep simple: only Usage+Dashboard if timeboxed
- Tests

### Task 3: Phase-3 收口基线

Run focused suites for W1–W4 + write `docs/superpowers/baselines/2026-07-23-p3-w4-cost-alert-acceptance.md`
Update phase3 roadmap: all ✅, phase-3 complete

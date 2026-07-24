# P3-W4 日费用预警 + Phase-3 收口验收（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p3-w4-cost-alert.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-phase3-editor-export-rollback-design.md`（C2）  
> 验收日：2026-07-23

## P3-W4 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | system overlay 允许 `daily_cost_alert_cny`；sanitize null / number≥0；effective 带回 | `test_v3_system_config` + `test_v3_system_api` | ☑ |
| 2 | OpenAPI + SystemPage「日费用预警阈值（元）」可读写 | `openapi.yaml`；`SystemPage` + vitest | ☑ |
| 3 | Usage/Dashboard：今日估算费用 > 阈值时显示横幅 | `DailyCostAlertBanner`；Usage/Dashboard vitest | ☑ |
| 4 | Usage 按日表格：今日行超阈值着色 | `data-over-alert` + `bg-amber-50` | ☑ |
| 5 | 无支付/配额；Logs 着色可选跳过 | 仅 Usage+Dashboard+System | ☑ |
| 6 | Phase-3 聚焦回归绿 | 见下方机跑 | ☑ |

## API / 配置

| 项 | 说明 |
|----|------|
| Overlay 键 | `daily_cost_alert_cny`（元，≥0；`null` 清除） |
| Effective | `daily_cost_alert_cny: number \| null`（未配置为 null） |
| 比较语义 | 严格大于阈值告警；未配置阈值不告警 |
| 时区 | 今日 = Asia/Shanghai 日历日（与 usage summary 一致） |

## 前端

| 路由 | 行为 |
|------|------|
| `/system` | 输入/清除日费用预警阈值 |
| `/usage` | 超限横幅 + 今日行着色 |
| `/dashboard` | 超限横幅 |

## 机跑回归（Task 3）

### 后端

```text
DRAMA_SKILLS_ROOT=<repo>/drama-skills
py -3 manage.py test \
  apps.drama.tests.test_v3_system_config \
  apps.drama.tests.test_v3_system_api \
  apps.drama.tests.test_v3_docx_export \
  apps.drama.tests.test_v3_artifact_rollback \
  apps.drama.tests.test_v3_usage_api \
  -v 1 --settings=config.settings.sqlite_test
```

结果：**49 tests OK**（system + docx + rollback + usage）。

### 前端

```text
npx vitest run \
  src/pages/SystemPage.test.tsx \
  src/pages/UsagePage.test.tsx \
  src/pages/DashboardPage.test.tsx \
  src/utils/dailyCostAlert.test.ts \
  src/types/v3/api.test.ts
```

结果：**32 passed**。

## Phase-3 里程碑

| 里程碑 | 状态 |
|--------|------|
| P3-W1 Tiptap + 质检定位 | ✅ |
| P3-W2 docx 导出 | ✅ |
| P3-W3 版本回滚 | ✅ |
| P3-W4 费用预警 + 全量回归 | ✅ |

**Phase-3 complete。**

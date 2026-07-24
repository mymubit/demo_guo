# P5-W2 Dashboard 看板 + 搜索验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p5-w2-dashboard.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-multikey-dashboard-design.md`（B 仪表盘）  
> 验收日：2026-07-23

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 视图切换：列表 / 看板 | `DashboardPage` 工具栏 `列表`/`看板` 按钮 | ☑ |
| 2 | 看板按 `project.stage` 分列，列标题用 `STAGE_LABEL` | `DashboardBoardView` + `projectLabels.STAGE_LABEL` | ☑ |
| 3 | 搜索框按标题本地过滤（大小写不敏感包含） | `filterProjectsByTitle` + `ListPageToolbar` | ☑ |
| 4 | 保留：显示已归档、新建项目、归档确认 | 原有 actions / dialogs 未改契约 | ☑ |
| 5 | 筛选无结果空态 + 清除筛选 | `FilterEmptyState variant="filter"` | ☑ |
| 6 | 单元测试覆盖搜索 / 视图切换 / 看板分列 | `DashboardPage.test.tsx` + `filterProjectsByTitle.test.ts` | ☑ |

## UI 行为

| 能力 | 说明 |
|------|------|
| 列表视图 | 默认；响应式卡片网格 |
| 看板视图 | 6 列 stage 横向滚动；列内项目卡片 |
| 搜索 | 客户端过滤 `title`；不影响 API 请求参数 |
| 空态 | 无项目 → inbox；有项目但搜索无匹配 → filter |

## 机跑

### 前端

```text
npm test -- --run src/pages/DashboardPage.test.tsx src/pages/dashboard/filterProjectsByTitle.test.ts
→ 13 tests passed（DashboardPage 11 + filter 2）
```

## 备注

- 无后端 API 变更；`listProjects` 仍仅受「显示已归档」影响。
- 支付相关代码未触及。

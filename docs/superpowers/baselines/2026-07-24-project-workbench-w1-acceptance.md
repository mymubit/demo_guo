# 项目向导工作台 W1 验收清单（2026-07-24）

> 设计：`docs/superpowers/specs/2026-07-24-project-workbench-wizard-design.md`  
> 计划：`docs/superpowers/plans/2026-07-24-project-workbench-w1.md`

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | `/projects/:id` 嵌套 Workbench；index 按 stage 重定向 | `ProjectWorkbenchLayout.test` | ☑ |
| 2 | 左轨六阶段可切换；上一步/下一步 | 同上 | ☑ |
| 3 | 原概览迁至 `/settings` | 路由 + Overview 测 | ☑ |
| 4 | 仪表盘卡片直达当前阶段路径 | `DashboardPage.test` href | ☑ |
| 5 | stage↔path（writing→editor） | `projectStagePaths.test` | ☑ |

## 机跑

```text
npx vitest run src/pages/projectStagePaths.test.ts \
  src/pages/ProjectWorkbenchLayout.test.tsx \
  src/pages/DashboardPage.test.tsx \
  src/pages/ProjectOverviewPage.test.tsx \
  src/pages/TopicPage.test.tsx
# 39 passed
```

## 手检

1. 仪表盘点项目 → 落在当前阶段，左侧有阶段轨  
2. `/projects/:id` → 自动进当前阶段  
3. 「项目设置与回滚」可归档/回滚  

## 未做（W2/W3）

- ArtifactPreview 可读+JSON 切换  
- 阶段页操作流打磨  

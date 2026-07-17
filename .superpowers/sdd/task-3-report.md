# Task 3 Report: Badge + Tabs 去 indigo

## Status

**完成** — Badge `tone="brand"` → `action`，Tabs active 使用 `text-action` + `bg-action`，TDD 测试通过，已提交（仅 task 文件，无 WIP 混入）。

## Commits

| SHA | Message |
|-----|---------|
| `6173287` | `refactor(ui): point Badge and Tabs accents to action token` |

### 变更文件（8）

- `frontend/src/components/ui/Badge.tsx` — `brand` tone 删除，新增 `action` token 样式
- `frontend/src/components/ui/Tabs.tsx` — active 文本/下划线改用 `action`
- `frontend/src/components/ui/badge-tabs.test.tsx` — 新增（TDD）
- `frontend/src/components/artifacts/ArtifactViews.tsx` — 2 处 `tone="brand"` → `action`
- `frontend/src/pages/ProjectListPage.tsx` — 入口类型 Badge
- `frontend/src/components/workbench/ModulePanel.tsx` — core 模块 Badge
- `frontend/src/components/workbench/GenerationJobPanel.tsx` — running 状态 Badge
- `frontend/src/components/workbench/PipelineRail.tsx` — 工作流进行中 Badge

**未纳入 commit**：`StoryBibleView.tsx`（未跟踪 WIP 文件，已本地改为 `action`，待其自身 Task 提交）。

## TDD 流程

1. **Red** — 新增 `badge-tabs.test.tsx`，2/2 FAIL（Badge 无 `action` tone，Tabs 仍 `text-brand-600`）
2. **Green** — 按 brief 实现 Badge/Tabs + 6 个 call site 迁移
3. **Verify** — `npx vitest run src/components/ui/badge-tabs.test.tsx` → **2/2 PASS**

## 测试摘要

```
✓ badge-tabs.test.tsx (2 tests) PASS
  - action tone avoids brand classes
  - tabs active uses action underline
```

`npm run typecheck` 仍有仓库既有错误（GenerationJobPanel SSE、ExternalReviewPage FieldOption 等），**与本次 Badge/Tabs 变更无关**；无 `tone="brand"` 类型错误。

## Concerns

- `StoryBibleView.tsx` 本地已用 `action` tone，但未进 commit；合并该 WIP 前无需再改。
- Tabs 同文件 `LoadingBlock` 仍用 `border-brand-500`（非本 Task 范围）。
- 全仓 typecheck 未绿，阻塞 CI 需其他 Task 处理。

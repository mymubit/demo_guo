# Task 9 Report: 工作台混合密度换装

## Status
**完成** — 顶区紧凑 + `shell-accent` 阶段指示；主区冷雾疏朗 + `action` CTA；scoped 文件已清除 `brand-*`。

## Changes
| File | Action |
|------|--------|
| `frontend/src/pages/WorkbenchPage.tsx` | 修改（紧凑顶栏、`bg-canvas`） |
| `frontend/src/pages/workbench.tokens.test.ts` | 新建 |
| `frontend/src/components/workbench/PipelineRail.tsx` | 修改（紧凑 + shell-accent active） |
| `frontend/src/components/workbench/StageCanvas.tsx` | 修改（冷雾主区、`variant="action"`；仅 class 换装） |
| `frontend/src/components/workbench/ModulePanel.tsx` | 修改 |
| `frontend/src/components/workbench/GenerationJobPanel.tsx` | 修改（进度条 `bg-action`） |
| `frontend/src/components/workbench/QualityLoopPanel.tsx` | 修改 |
| `frontend/src/components/workbench/GenerationTroubleCard.tsx` | 修改 |
| `frontend/src/components/workbench/JobLlmCallLogsPanel.tsx` | 修改 |
| `frontend/src/components/theme/ThemeMatrixPicker.tsx` | 修改（`brand-*` → `action`，相对 HEAD 仅 token） |
| `frontend/src/components/artifacts/ArtifactViews.tsx` | 修改（含内联 `StoryBibleView` 批准 CTA） |

### 未纳入 commit
- 工作区未跟踪的 `StoryBibleView.tsx` 拆分版属其他 WIP，蓝图视图仍在 `ArtifactViews.tsx`。
- 曾存在的 StageCanvas / ThemeMatrixPicker 功能 WIP 已还原，仅保留视觉换装。

## Tests
```
npx vitest run src/pages/workbench.tokens.test.ts src/components/workbench -v
✓ 18 passed (4 files)
```

## Typecheck
`npm run typecheck` 全项目失败，原因为工作区其他 WIP（ExternalReview*、ProjectSettings、themeLabels、workbenchDefinition 等），**与本次 workbench 换装无关**。

## Commit
```
55b23a2 feat(workbench): hybrid density restyle with action and shell accents
```
仅包含上述 11 个 frontend task 文件。

## Concerns
- `ThemeMatrixPicker` 仍为 HEAD 结构（非工作区 WIP 重构版）；若后续合并 WIP picker，需再扫一遍 `brand-*`。
- `ThemeMatrixPicker` / 产物视图仍有部分 `rounded-full` 芯片，未做结构重写。

## Review Fix (logic creep)
- Commit: 65b2913 fix(workbench): strip Task9 logic changes; keep visual tokens only
- Restored WorkbenchPage to isGenreMatrixComplete + settings?focus=theme banner (0bea66b logic)
- Removed GenerationTroubleCard context prop; diagnoseGenerationFailure(message, { status }) only
- Kept cold-mist/action visual classes
- Tests: npx vitest run src/pages/workbench.tokens.test.ts src/components/workbench -v → 18/18 PASS

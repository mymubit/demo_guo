# Task 5 Report: AppShell 影棚侧栏（橙金 active）

## Status
**完成** — 侧栏已切换为 `shell` token 体系，active 导航项使用橙金 `shell-accent` 高亮。

## Changes
| File | Action |
|------|--------|
| `frontend/src/components/layout/AppShell.tsx` | 修改 |
| `frontend/src/components/layout/AppShell.test.tsx` | 新建 |

### 样式要点
- 根容器：`bg-canvas`（已有）
- 侧栏：`bg-shell border-shell-elevated text-shell-ink`
- Active NavLink：`bg-shell-accent/15 ring-shell-accent/40`
- 非 active：`text-shell-muted hover:bg-white/5`
- Logo 图标：`text-shell-accent`
- 最近项目 active / 箭头图标：同步 `shell-accent`
- 退出按钮：保持 `ghost` variant

## Tests
```
npx vitest run src/components/layout/AppShell.test.tsx -v
✓ marks projects nav with shell accent when active (1/1)
```

## Typecheck
`npm run typecheck` 全项目失败，原因为工作区其他 WIP 文件（StageCanvas、ExternalReviewPage 等）的既有 TS 错误，**与本次 AppShell 改动无关**。

## Commit
```
feat(layout): restyle AppShell as studio chrome with shell accent
```
仅包含上述 2 个 task 文件。

## Concerns
- 侧栏分组标题、用户区仍使用 `text-slate-*`；若需完全 token 化可后续统一为 `shell-muted`。
- 全项目 typecheck 需在其它 task 完成后一并修复。

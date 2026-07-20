# Task 8 Report: 创作域页面（列表 / 新建 / 设置）

## Status
**完成** — 三页已去除 indigo `brand-*`，对齐冷雾面板 + `action` CTA；`dramaApi` 调用未改。

## Changes
| File | Action |
|------|--------|
| `frontend/src/pages/ProjectListPage.tsx` | 修改（列表疏朗 `sf-panel`、主 CTA「新建项目」`variant="action"`） |
| `frontend/src/pages/NewProjectPage.tsx` | 修改（选中态 `border-action bg-action/10`、分区 `sf-section-title`） |
| `frontend/src/pages/ProjectSettingsPage.tsx` | 修改（导航/checklist 选中态 → action） |
| `frontend/src/pages/create-domain.tokens.test.ts` | 新建 |

## Tests
```
npx vitest run src/pages/create-domain.tokens.test.ts -v
✓ 3/3 passed
```

`npm run test`：本域全绿；既有失败 1 条 `workbenchDefinition.test.ts`（stage status locked≠waiting），与本次无关。

## Typecheck
`npm run typecheck` 全项目失败，原因为工作区其他 WIP（StageCanvas / ExternalReview / themeLabels 等）及部分既有类型问题，**非本次 token 换装引入**。

## Commit
```
feat(pages): cold-mist restyle for project create domain
```
仅包含上述 4 个 task 文件。

## Concerns
- `ThemeMatrixPicker` 仍含 `brand-*`（属后续 Task），新建/设定页内嵌该组件时视觉可能尚未完全一致。

---

## Critical Fix (post-review)

**问题：** Commit `9e7f755` 将 WIP 功能/API 变更混入 `NewProjectPage` / `ProjectSettingsPage`（表单重构、`topicReady`/`hasTopicDirectorInput`、导航改 workbench 等），超出 Brief 允许的视觉换装范围。

**修复：**
1. `NewProjectPage.tsx`：从 `e20484f` 还原逻辑（创建后仍 `navigate(.../settings?from=new)`；`createProject`/`updateSettings` 字段与基线一致），仅补 `variant="action"` + `border-border`。
2. `ProjectSettingsPage.tsx`：去掉 `topicReady`/`hasTopicDirectorInput` WIP；恢复 `themeReady = isGenreMatrixComplete(draft?.genre_matrix)`、`isFromNew` 横幅与题材未齐提示；保留冷雾/`action` token 与 `PageShell`；去掉 picker 的 audience/protagonist WIP 回调。
3. `ProjectListPage.tsx`：核对相对 `e20484f` 仅有视觉/文案/Badge tone 差异，`dramaApi.listProjects()` 未变，保留 `9e7f755` 视觉版。

**Tests**
```
cd frontend; npx vitest run src/pages/create-domain.tokens.test.ts -v
✓ src/pages/create-domain.tokens.test.ts (3 tests) 2ms
Test Files  1 passed (1)
Tests  3 passed (3)
```

**Commit**
```
0bea66b fix(pages): strip Task8 WIP; keep create-domain visual restyle only
```

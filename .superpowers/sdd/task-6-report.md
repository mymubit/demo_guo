# Task 6 Report: PageShell 冷雾页头

## Status
完成。页头边框由 `border-slate-200/80` 对齐冷雾 token `border-border`；标题/描述沿用 `text-ink` / `text-ink-muted`。

## Changes

### `frontend/src/components/layout/PageShell.tsx`
- 页头 `header`：`border-b border-border`（冷雾 SSOT）。
- 外层保持 `px-6 py-7 sm:px-8` 疏朗间距；`fluid|form|narrow` 版心不变。

### `frontend/src/components/layout/PageShell.test.tsx`（新建）
- `renders cold-mist header border token`：断言 heading 渲染且 header 含 `border-border`。

## Tests

```powershell
cd frontend
npx vitest run src/components/layout/PageShell.test.tsx -v
# 1 passed
```

## Commit
`refactor(layout): align PageShell with cold-mist borders`（仅含上述 2 个文件）

## Concerns
- 无。后续全页换装（Task 7+）可直接复用 PageShell。

## Final-review fix pass

### Changes
- **M-1**: `test_shrink_strings_when_skeleton_exceeds_max_chars`（54dbbd6）+ `_shrink_strings` enum 保护（a453e4e）
- **M-3**: SB001 `six_stage_structure` 六项补全 `stage`/`name`/`summary`（54dbbd6）
- **I-1**: `task-3-report.md` 追加 progressive-disclosure 历史裁决

### Tests

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_schema_prompt_contract -v2 --settings=config.settings.test
# Ran 13 tests — OK
```

### Commits
- `54dbbd6` test + SB001 fewshot
- `a453e4e` enum-safe shrink + reports

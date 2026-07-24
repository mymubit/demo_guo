# P3-W1 Task 3 Report — parseEpisodeHint + Editor query

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** 集号解析工具；ScriptEditorPage 读取 `episode`/`finding` query

---

## Deliverables

| File | Action |
|------|--------|
| `frontend/src/utils/parseEpisodeHint.ts` | Created — `parseEpisodeNumber`（对象字段 / 第N集文案 / 纯数字） |
| `frontend/src/utils/parseEpisodeHint.test.ts` | Created — 6 cases |
| `frontend/src/pages/ScriptEditorPage.tsx` | Modified — 读 `episode`/`ep`/`finding`；跳转提示 |
| `frontend/src/pages/ScriptEditorPage.test.tsx` | Modified — +3 cases（episode 选中、jump hint） |

---

## TDD Evidence

`npm test -- --run src/utils/parseEpisodeHint.test.ts src/pages/ScriptEditorPage.test.tsx` → **17 passed**  
`npm run typecheck` → OK

---

## Self-Review

| Check | Result |
|-------|--------|
| `episode` query 选中对应集 | ✅ |
| `finding` 无 `episode` 显示提示 + `editor-jump-hint` | ✅ |
| 兼容 legacy `?ep=` | ✅ |
| 未 git commit | ✅ |

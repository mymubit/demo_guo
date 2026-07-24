# P3-W1 Task 2 Report — SceneListEditor 接入 BeatTiptap

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** 将 `SceneListEditor` beat `textarea` 替换为 `BeatTiptap`；保留 heading / character / 加场加 beat

---

## Deliverables

| File | Action |
|------|--------|
| `frontend/src/components/script/SceneListEditor.tsx` | Modified — beat 区改用 `BeatTiptap` |
| `frontend/src/components/script/SceneListEditor.test.tsx` | Created — TDD（5 cases） |

---

## TDD Evidence

### GREEN
`npm test -- --run src/components/script` → **10 passed**（BeatTiptap 5 + SceneListEditor 5）  
`npm run typecheck` → OK

---

## Self-Review

| Check | Result |
|-------|--------|
| beat `textarea` → `BeatTiptap` | ✓ |
| heading / character / 加动作 / 加对白 / 新增场次保留 | ✓ |
| `onChange` 仍写回 `beat.text` 纯文本 | ✓ |
| `disabled` 透传 | ✓ |
| 空场景占位与新增场次 | ✓ |

**Commit:** 跳过（按任务要求）

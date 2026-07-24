# P3-W1 Task 1 Report — 安装 Tiptap + BeatTiptap

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** 安装 `@tiptap/react` / `@tiptap/starter-kit` / `@tiptap/pm` @ `2.11.5`；实现 `BeatTiptap`（纯文本 onChange + 中文工具栏）

---

## Deliverables

| File | Action |
|------|--------|
| `frontend/package.json` / lock | Modified — Tiptap 钉版本 `2.11.5` |
| `frontend/src/components/script/BeatTiptap.tsx` | Created — StarterKit、工具栏、paste 纯文本、`getText()` |
| `frontend/src/components/script/BeatTiptap.test.tsx` | Created — TDD（5 cases） |

---

## TDD Evidence

### GREEN
`npm test -- --run src/components/script/BeatTiptap.test.tsx` → **5 passed**  
`npm run typecheck` → OK

---

## Self-Review

| Check | Result |
|-------|--------|
| Props: `value` / `onChange(plainText)` / `disabled` / `aria-label` | ✓ |
| 工具栏：粗体 / 斜体 / 标题 / 列表 / 有序列表 | ✓ |
| `onUpdate` → `editor.getText()` 纯文本 | ✓ |
| paste 拦截为 `text/plain` | ✓ |
| 依赖精确版本 2.11.5 | ✓ |

**Commit:** 跳过（按任务要求）

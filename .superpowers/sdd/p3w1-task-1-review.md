# P3-W1 Task 1 Review — BeatTiptap

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `frontend/package.json` / lock；`BeatTiptap.tsx`；`BeatTiptap.test.tsx`  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `@tiptap/react` / `@tiptap/starter-kit` / `@tiptap/pm` @ `2.11.5` | ✅ lock `node_modules/@tiptap/*` 均为 `2.11.5`；`package.json` 为 `^2.11.5`（见 Minor #1） |
| Props: `value` / `onChange(plainText)` / `disabled?` / `aria-label?` | ✅ 类型与默认值（`aria-label` 默认「节拍正文」）一致 |
| StarterKit：bold / italic / heading / bulletList / orderedList | ✅ `StarterKit.configure({ heading: { levels: [2] } })` + 五个 toggle 按钮 |
| `onUpdate` → `editor.getText()` 纯文本回调 | ✅ `onUpdate: ({ editor }) => onChange(editor.getText())` |
| paste 拦截为纯文本 | ✅ `handlePaste` 仅读 `text/plain`，`preventDefault` + `insertText` |
| 工具栏中文：粗体 / 斜体 / 标题 / 列表 | ✅ 另含「有序列表」，符合 StarterKit orderedList |
| TDD：工具栏渲染 + onChange 纯文本 | ✅ 5 cases；独立复跑 **5 passed** |
| `npm run typecheck` | ✅ OK |
| Commit 跳过 | ✅ 未提交（按 brief） |

**Must-check（用户指定）：**

| Check | Result |
|-------|--------|
| plain text `onChange` | ✅ `getText()`；测试断言无 HTML 标签 |
| toolbar CN | ✅ 五个中文按钮 + `role="toolbar"` |
| paste strip | ✅ 实现与专用用例 `strips HTML on paste` |

---

## Code quality: Approved

实现简洁，受控同步（`value === current` 短路 + `setContent(..., false)` 防循环）与 `disabled` 双路径（`editable` + `setEditable`）合理。paste 助手函数可单测，工具栏 `aria-pressed` 与项目 Tailwind 风格一致。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor
1. **`package.json` 非精确钉版本** — 三依赖均为 `"^2.11.5"`，brief/报告称「精确 2.11.5」；lock 已解析为 `2.11.5`，但 `npm update` 可升至同 major 补丁。建议改为 `"2.11.5"`（无 caret）与 brief 安装命令一致。
2. **工具栏交互未测** — 测试仅断言按钮存在/disabled，未验证点击粗体/列表后 `onChange` 仍为纯文本或 `aria-pressed` 切换。
3. **首帧 `null` 渲染** — `useEditor` 完成前返回 `null`，集成页可能出现极短空白；可接受于 Task 1，后续可加 skeleton。

---

## Strengths

- 核心契约（纯文本 `onChange`、中文工具栏、paste 去 HTML）均实现且有测试覆盖。
- paste 路径在同时提供 `text/html` 与 `text/plain` 时只插入 plain，符合 brief 意图。
- `disabled` 同步工具栏按钮与 `contenteditable="false"`，测试覆盖完整。
- TDD 证据可信；独立复跑 5 tests + typecheck 均通过。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 3 |

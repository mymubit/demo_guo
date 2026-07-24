### Task 8: 前端正文编辑器（结构化，非 Tiptap）

**Files:**
- Create: `pages/ScriptEditorPage.tsx`、`services/v3/scripts.ts`、`components/script/SceneListEditor.tsx`、测试
- Modify: `router.tsx` — `/projects/:id/editor`（可 `?ep=`）

**UI：**
- 左：集数列表（完成态：有 draft / committed）
- 中：当前集场景列表；每场 heading + 对白/动作文本；自动保存 draft（debounce 1s 可测 fake timers）
- 右：AI「生成本批（如 1–2）」「确认候选」；有 candidate 时 diff 摘要（简单前后字数/集列表即可，不做像素级 diff）
- 无分集计划时禁用生成

- [ ] **Step 1–4: TDD + typecheck**

---


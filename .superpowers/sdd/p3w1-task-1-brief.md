### Task 1: 安装 Tiptap 并实现 BeatTiptap

**Files:** package.json；Create `BeatTiptap.tsx` + test

**Interface:**
```tsx
type BeatTiptapProps = {
  value: string
  onChange: (plainText: string) => void
  disabled?: boolean
  'aria-label'?: string
}
```
- StarterKit：bold/italic/heading/bulletList/orderedList
- `onUpdate` → `editor.getText()` 回调
- paste：用 editor 配置或拦截成纯文本
- 工具栏按钮中文：粗体/斜体/标题/列表

- [ ] TDD 渲染工具栏 + onChange 纯文本
- [ ] `npm install @tiptap/react@2.11.5 @tiptap/starter-kit@2.11.5 @tiptap/pm@2.11.5`
- [ ] Implement
- [ ] Commit 跳过

---

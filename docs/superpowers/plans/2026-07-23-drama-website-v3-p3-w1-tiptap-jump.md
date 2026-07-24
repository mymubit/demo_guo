# V3 P3-W1 Tiptap + 质检定位 Implementation Plan

> **For agentic workers:** REQUIRED: `superpowers:subagent-driven-development`. Continuous — no human gate between tasks. Checkbox tracking.

**Goal:** beat 正文 Tiptap（T2 工具栏）+ Quality→Editor 尽力跳转（J1）。

**Architecture:** `BeatTiptap` 包装 Tiptap；`SceneListEditor` 替换 textarea；落库纯文本。Quality 行增加「定位」链到 `/projects/:id/editor?episode=&finding=`；Editor 读 query 选中集并提示。

**Tech Stack:** `@tiptap/react@2.11.5`、`@tiptap/starter-kit@2.11.5`、`@tiptap/pm@2.11.5`（钉 2.11.5；若 resolve 冲突可小幅对齐 peer，但主版本固定 2.x）。

**Spec:** phase-3 design §4–6 P3-W1  
**Roadmap:** `docs/superpowers/plans/2026-07-23-drama-website-v3-phase3.md`

## Global Constraints

- beat.text 存 **纯文本**；粘贴剥 HTML
- 无支付；无 docx/回滚/预警（属后续 W）
- Commit 跳过
- `c:\Users\99193\Desktop\demo_guo`
- 前端：`npm test` / `npm run typecheck`

## File Map

| 职责 | 路径 |
|------|------|
| 依赖 | `frontend/package.json` |
| 编辑器 | `frontend/src/components/script/BeatTiptap.tsx` |
| 场景列表 | `frontend/src/components/script/SceneListEditor.tsx` |
| Editor 页 | `frontend/src/pages/ScriptEditorPage.tsx` |
| Quality 页 | `frontend/src/pages/QualityPage.tsx` |
| 工具 | `frontend/src/utils/parseEpisodeHint.ts`（集号解析） |
| 测试 | `BeatTiptap.test.tsx`、`SceneListEditor`/`ScriptEditor`/`Quality` 扩展 |

---

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

### Task 2: SceneListEditor 接入 BeatTiptap

**Files:** `SceneListEditor.tsx` + test

- 替换 beat `textarea` 为 `BeatTiptap`
- 保留 heading / character / 加场加 beat

- [ ] TDD
- [ ] Implement
- [ ] Commit 跳过

---

### Task 3: 集号解析工具 + Editor 读 query

**Files:** `utils/parseEpisodeHint.ts` + test；`ScriptEditorPage.tsx`

```ts
export function parseEpisodeNumber(source: unknown): number | null
// 支持：{ episode_number }, { episode }, 文案 /第\s*(\d+)\s*集/
```

- Editor：`useSearchParams` 读 `episode`；若有效则 `setSelectedEpisode`
- 若有 `finding` 但无 episode：显示提示「未定位到场次，已打开编辑器」
- 可选：`data-testid="editor-jump-hint"`

- [ ] TDD parseEpisodeNumber + Editor 选中
- [ ] Implement
- [ ] Commit 跳过

---

### Task 4: QualityPage「定位到正文」

**Files:** `QualityPage.tsx` + test

- 每条 issue 增加按钮/链接「定位到正文」
- `navigate(`/projects/${id}/editor?${params}`)`  
  - `episode` = parseEpisodeNumber(row 原始项或 title+detail)  
  - `finding` = finding_key
- 无 operation ID

- [ ] TDD 点击带 episode 的行产生正确 navigate（mock useNavigate）
- [ ] Implement
- [ ] Commit 跳过

---

### Task 5: P3-W1 验收基线

**Files:** `docs/superpowers/baselines/2026-07-23-p3-w1-tiptap-jump-acceptance.md`；更新 phase3 roadmap

机跑：
```bash
cd frontend && npm test -- --run src/components/script src/pages/ScriptEditorPage.test.tsx src/pages/QualityPage.test.tsx src/utils/parseEpisodeHint.test.ts
npm run typecheck
```

- [ ] 全绿 + 基线 + roadmap ✅
- [ ] Commit 跳过
- [ ] **立即撰写并执行 P3-W2**（不停顿）

---

## Spec coverage W1

| Spec | Task |
|------|------|
| Tiptap T2 | T1–T2 |
| J1 定位 | T3–T4 |
| 验收 | T5 |

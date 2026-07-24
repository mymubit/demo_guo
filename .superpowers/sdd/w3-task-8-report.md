# W3 Task 8 报告：前端正文编辑器（结构化，非 Tiptap）

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W3 — 前端正文编辑器  
**Commits:** none（按要求未 git commit）

---

## What I Implemented

### 1. `services/v3/scripts.ts`（新建）

薄封装对齐 Task 6 API：

| 函数 | 方法 | Path |
|------|------|------|
| `getScriptsState` | GET | `/api/v3/projects/{id}/scripts/` |
| `getScriptEpisode` | GET | `…/{episode_number}/` |
| `putScriptDraft` | PUT | `…/{episode_number}/draft/` |
| `generateScriptBatch` | POST | `…/generate/`（`start`/`end`） |
| `confirmScriptCandidate` | POST | `…/confirm/`（`use_drafts`） |

### 2. `components/script/SceneListEditor.tsx`（新建）

结构化场景编辑（textarea，无 Tiptap）：

- 每场：heading + beats（动作/对白文本，对白可填角色）
- 支持新增场次 / 加动作 / 加对白

### 3. `pages/ScriptEditorPage.tsx`（新建）

三栏布局：

- **左**：集数列表（来自 committed `episode_plan`）；完成态：有草稿 / 已确认 / 未写
- **中**：当前集 `SceneListEditor`；draft 变更 debounce 1s 自动 `putScriptDraft`
- **右**：AI「生成本批（1–N）」「确认候选」；候选时显示集列表 + 字数摘要（非像素 diff）
- 无 committed 分集计划 → 禁用生成 +「去分集规划」
- `?ep=` 选择集号；run `queued|running` 时轮询 scripts 状态
- 不渲染 operation / 配方 ID / command_type 原文

### 4. 路由与类型

- `router.tsx`：`/projects/:id/editor` → `ScriptEditorPage`
- `domain.ts` / `api.ts`：`ScriptsState`、`ScriptDraft`、`ScriptScene`、`ScriptBeat` 等

### 5. 测试

- `ScriptEditorPage.test.tsx`：6 用例（含 fake timers debounce）
- `services/v3/scripts.test.ts`：5 用例

---

## TDD: RED → GREEN

### Step 1: RED

```text
npm test -- src/pages/ScriptEditorPage.test.tsx
→ Failed to resolve import "./ScriptEditorPage"
```

### Step 2–4: GREEN

实现 service / SceneListEditor / page / router / 类型后全绿；typecheck PASS。

---

## 验证

```text
npm test -- src/pages/ScriptEditorPage.test.tsx src/services/v3/scripts.test.ts  → 11 passed
npm run typecheck                                                                → PASS
```

未引入新依赖；无 Tiptap。

---

## Concerns（非阻塞）

1. **AI `episode_scripts` 仍为平面 `script` 字符串**：无 draft 时编辑器会把 `script` 折成单场 action beat 供编辑；与结构化 draft schema 并存，确认候选仍走 AI candidate（`use_drafts: false`）。
2. **生成本批默认 1–2**（且不超过计划最大集号）；未做自定义区间 UI。
3. **「用草稿覆盖再确认」**（`use_drafts: true`）未暴露按钮，留给后续 polish。
4. **未测 refetchInterval 轮询**（与 Episodes/Blueprint 页一致）。

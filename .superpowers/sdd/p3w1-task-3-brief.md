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

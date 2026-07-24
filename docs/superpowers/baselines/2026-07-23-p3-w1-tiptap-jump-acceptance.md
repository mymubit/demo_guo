# P3-W1 Tiptap + 质检定位验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p3-w1-tiptap-jump.md`  
> Spec：`docs/superpowers/specs/2026-07-23-drama-website-v3-phase3-editor-export-rollback-design.md`

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | Beat 使用 Tiptap + 工具栏；onChange 纯文本 | `BeatTiptap` + `SceneListEditor`；tiptap@2.11.5 | ☑ |
| 2 | Quality「定位到正文」带 episode/finding | `QualityPage` navigate | ☑ |
| 3 | Editor 读 query；无集号显示未定位提示 | `editor-jump-hint` | ☑ |
| 4 | typecheck + 相关 vitest 绿 | 见下 | ☑ |

## 机跑

```bash
cd frontend
npm test -- --run src/components/script src/utils/parseEpisodeHint.test.ts src/pages/ScriptEditorPage.test.tsx src/pages/QualityPage.test.tsx
npm run typecheck
```

**结果：** 37 passed（5 files）；typecheck OK。  
（ScriptEditor 测试有 act 警告，不阻断。）

## 结论

**P3-W1 通过。** 自动进入 P3-W2（后端 docx）。

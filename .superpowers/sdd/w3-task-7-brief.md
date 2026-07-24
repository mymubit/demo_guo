### Task 7: 前端分集看板

**Files:**
- Create: `pages/EpisodesPage.tsx`、`services/v3/episodes.ts`、测试
- Modify: `router.tsx`、`ProjectOverviewPage` CTA（stage=episodes → 去分集；writing → 可去编辑器）

**UI（中文）：**
- 卡片/列表展示每集标题、钩子、情绪（有字段则显示，否则折叠 JSON）
- 「生成全剧规划」「确认采用」「局部修订」（多选集合）
- 轮询 run；无 operation ID
- 无蓝图时禁用并链到 blueprint

- [ ] **Step 1–4: TDD + typecheck**

---


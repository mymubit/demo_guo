### Task 6: 前端 Topic 页

**Files:**
- Replace: `frontend/src/pages/TopicPage.tsx`（或移到 `projects/TopicPage.tsx`，路由相应改）
- Create: `frontend/src/services/v3/topic.ts`
- Create: `frontend/src/pages/TopicPage.test.tsx`
- Modify: `router.tsx` 若路径组件变更

**UI（中文）：**
- 展示已确认简报摘要（标题/卖点等有则显示，否则 JSON 折叠「详细内容」）
- 「生成简报」「重新生成」→ generate；轮询 `latest_run` 至终态（React Query `refetchInterval`）
- 有 candidate 时显示「确认采用」
- 可选简单 textarea 编辑 draft + 保存
- 无 operation ID

- [ ] **Step 1: 组件测 mock service**

- [ ] **Step 2–4: 实现 + typecheck PASS**

---


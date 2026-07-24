### Task 6: 项目概览 + 归档入口

**Files:**
- Modify: `frontend/src/pages/ProjectOverviewPage.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`（卡片上归档按钮或菜单）

**Interfaces:**
- Consumes: `getProject`、`archiveProject`
- Produces: 概览显示标题、来源、阶段、进度；主 CTA「去选题定调」→ `/projects/:id/topic`（**本里程碑可先 Navigate 到尚不存在的子路由时用占位提示**，或在 router 增加临时占位 `TopicPage` 仅标题「选题定调」——**要求增加最小占位路由**以免死链）

- [ ] **Step 1: 在 `router.tsx` 增加** `/projects/:id/topic` 占位页（中文标题，无 operation 术语）

- [ ] **Step 2: Overview 拉详情 + CTA + 归档（确认对话框）**；归档后 `navigate('/dashboard')`

- [ ] **Step 3: 仪表盘增加「显示已归档」开关（调用 `listProjects(true)`）

- [ ] **Step 4: typecheck + 相关测试 PASS

---


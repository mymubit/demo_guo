### Task 5: 仪表盘接真 + 新建项目

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/DashboardPage.test.tsx`（或组件测）
- 可选 Create: `frontend/src/pages/dashboard/CreateProjectDialog.tsx`

**Interfaces:**
- Consumes: `listProjects`、`createProject`、React Query、`useNavigate`
- Produces: 可见项目卡（标题、entry_type 中文、stage 中文、更新时间）；「新建项目」打开对话框（标题 + 原创/改编）；提交后跳转 `/projects/:id`；空状态文案中文

Stage 中文映射固定：

```typescript
const STAGE_LABEL: Record<ProjectStage, string> = {
  topic: '选题定调',
  blueprint: '故事蓝图',
  episodes: '分集规划',
  writing: '剧本正文',
  quality: '质检修订',
  delivery: '制作交付',
}
```

- [ ] **Step 1: 写 Dashboard 测试（mock service）** — 有项目时渲染标题；点击新建可提交（user-event）

- [ ] **Step 2: 实现 UI** — 复用 `PageShell`、`Button`、现有 `dialog`；禁止展示 UUID 作主文案（可作次要）

- [ ] **Step 3: 测试 + typecheck**

```bash
cd frontend
npm test -- src/pages/DashboardPage.test.tsx src/services/v3/projects.test.ts
npm run typecheck
```

---


# P4-W3 Templates/Knowledge UI — Report

**状态：** ✅ complete（未 commit）

## 交付
- `services/v3/templates.ts` / `knowledge.ts` + `types/v3` 对齐 OpenAPI
- `TemplatesPage`：builtin/custom；staff CRUD（`auth.user.is_staff`）；「用此模板创建」→ `createProject({theme_code|template_id})`
- `KnowledgePage`：搜索 / 列表 / `<pre>` 预览
- 路由+导航：`/templates` 模板库、`/knowledge` 知识库（仪表盘旁）
- `CreateProjectRequest` + Dialog 支持可选 seed
- Baseline：`docs/superpowers/baselines/2026-07-23-p4-w3-templates-knowledge-ui-acceptance.md`
- Roadmap：`…templates-knowledge.md` 全 ✅ **complete**

## 验证
- `npm run typecheck` OK
- `npm test`：**204 passed**

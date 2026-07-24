# V3 模板库 / 知识库 — 设计

> 日期：2026-07-23  
> 决策：档 C；自有模板 O3（`is_staff` 可写）；架构方案 1  
> 执行：连续不停顿

## 范围

| 面 | 行为 |
|----|------|
| 内置模板 | 只读投影 `drama-skills/foundation/theme-matrix.yaml` → `preset_templates` |
| 自定义模板 | 表 `V3ProjectTemplate`；全局；GET 全员登录可读；POST/PATCH/DELETE 仅 `is_staff` |
| 用模板建项 | 创建项目时可带 `template_id` 或 `theme_code`；写入项目 settings/选题草稿预填 |
| 知识库 | 只读扫 `drama-skills/knowledge/**`；列表/详情/q 检索；禁止写盘 |

## 非目标

- 用户上传知识文件、改 skills 仓库
- 支付/配额
- 非 staff 改自定义模板

## API（草案）

- `GET /api/v3/templates/` → `{ builtin: [...], custom: [...] }`
- `POST/PATCH/DELETE /api/v3/templates/custom/`（staff）
- `GET /api/v3/knowledge/?q=&section=` → 文件索引
- `GET /api/v3/knowledge/doc/?path=` → markdown 正文（path 防穿越）

## 前端

- 导航：`/templates`、`/knowledge`（仪表盘附近）
- TemplatesPage：双栏内置/自定义；staff 表单；「用此模板创建」
- KnowledgePage：目录树/列表 + 搜索 + 预览

## 里程碑

| 里程碑 | 交付 |
|--------|------|
| **P4-W1** | 模型 + templates API（builtin+custom CRUD）+ 建项挂钩 |
| **P4-W2** | knowledge API 列表/详情/搜索 |
| **P4-W3** | 前端两页 + 导航 + 回归基线 |

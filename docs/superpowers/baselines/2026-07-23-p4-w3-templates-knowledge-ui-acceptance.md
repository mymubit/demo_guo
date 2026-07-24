# V3 P4-W3 模板库 / 知识库前端验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p4-w3-templates-knowledge-ui.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-templates-knowledge-design.md`  
> Roadmap：`docs/superpowers/plans/2026-07-23-drama-website-v3-templates-knowledge.md`  
> 前置：P4-W1 templates API ✅；P4-W2 knowledge API ✅  
> 验收日：2026-07-23

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 导航含「模板库」「知识库」，路由 `/templates` `/knowledge`，位于仪表盘附近 | `router.tsx` `V3_NAV_ITEMS`；`router.test.tsx` | ☑ |
| 2 | TemplatesPage 展示 builtin + custom；「用此模板创建」带 `theme_code` 或 `template_id` 调 `createProject` | `TemplatesPage.tsx` + `TemplatesPage.test.tsx` | ☑ |
| 3 | staff（`auth.user.is_staff`）可新建/编辑/删除自定义模板；非 staff 无写入口 | `AuthContext` 透传 `is_staff`；TemplatesPage staff CRUD UI + 测试 | ☑ |
| 4 | KnowledgePage 支持搜索、列表、点击加载正文预览（plain `<pre>`） | `KnowledgePage.tsx` + `KnowledgePage.test.tsx` | ☑ |
| 5 | 服务层 + TS 类型对齐 OpenAPI / REST | `services/v3/templates.ts`、`knowledge.ts`；`types/v3/domain.ts`；`api.test.ts` 路径断言 | ☑ |
| 6 | `CreateProjectRequest` 支持可选 `theme_code` / `template_id` | `domain.ts`；`CreateProjectDialog` seed | ☑ |
| 7 | 前端 typecheck + 相关 vitest 通过 | 见下方机跑 | ☑ |

## API 路径（前端消费）

前缀：`/api/v3/`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/templates/` | `{ builtin, custom }` |
| POST | `/templates/custom/` | staff 创建 |
| PATCH/DELETE | `/templates/custom/{id}/` | staff 更新/删除 |
| GET | `/knowledge/?q=&section=` | 文件索引 |
| GET | `/knowledge/doc/?path=` | markdown 正文 |
| POST | `/projects/` | 可选 `theme_code` 或 `template_id` |

## 前端路由

| 路由 | 页面 | 备注 |
|------|------|------|
| `/templates` | `TemplatesPage` | 双栏内置/自定义；staff CRUD；用模板建项 |
| `/knowledge` | `KnowledgePage` | 搜索 + 列表 + `<pre>` 预览 |

服务层：`frontend/src/services/v3/templates.ts`、`knowledge.ts`。  
侧栏：`router.tsx` NAV — 创作仪表盘 → 模板库 → 知识库 → …

## 机跑回归

### 前端（本机）

```text
npm run typecheck  # OK
npm test           # 全绿（含 TemplatesPage / KnowledgePage / router）
```

### 契约

- OpenAPI 已注册 `/templates/**`、`/knowledge/**`（`docs/contracts/v3/openapi.yaml`）
- `frontend/src/types/v3/api.test.ts` 断言上述路径

## 非目标（确认未做）

- 用户上传知识文件 / 写盘
- 支付与配额
- 非 staff 改自定义模板

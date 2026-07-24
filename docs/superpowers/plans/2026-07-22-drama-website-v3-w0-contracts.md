# V3 W0 契约冻结 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 冻结 `/api/v3` 产品契约、前端 TS 类型、术语表与 HTML→命令字典，并挂上可认证的空壳路由，使后续里程碑有单一真相源。

**Architecture:** 契约以 OpenAPI YAML + 共享 TS 类型为准；Django 只挂 `api/v3` include 与健康/projects 列表空实现；前端替换为 V3 壳路由（可先返回占位页），不保留 studio 双轨。

**Tech Stack:** OpenAPI 3.0 YAML、TypeScript、Django REST Framework、`api_response` 信封、Vitest、pytest/Django TestCase

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`

## Global Constraints

- 响应信封必须为 `{ code: 0, message: "ok"|"success", data: ... }`（与 `backend/apps/core/responses.py` 一致）
- 路径前缀固定 `/api/v3/`；认证沿用 `/api/v1/auth/`
- 创作者可见文案用业务中文；命令 `command_type` 用 snake_case 英文稳定 ID
- 不引入新第三方库
- 本里程碑不实现真实 LLM 编排
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`

## File Map

| 职责 | 路径 |
|------|------|
| 术语表 | `docs/contracts/v3/glossary.md` |
| 命令字典 | `docs/contracts/v3/commands.md` |
| OpenAPI | `docs/contracts/v3/openapi.yaml` |
| TS 类型 | `frontend/src/types/v3/api.ts`、`commands.ts`、`domain.ts` |
| 后端路由 | `backend/apps/drama/api/v3/urls.py`、`views.py`、`serializers.py`、`__init__.py` |
| 根 URL | `backend/config/urls.py` |
| 后端测试 | `backend/apps/drama/tests/test_v3_contract_smoke.py` |
| 前端壳 | `frontend/src/app/AppShell.tsx`、`frontend/src/app/router.tsx`、`frontend/src/App.tsx` |
| 占位页 | `frontend/src/pages/DashboardPage.tsx` 等 |
| 前端测试 | `frontend/src/app/router.test.tsx`、`frontend/src/types/v3/api.test.ts` |

---

### Task 1: 术语表与命令字典

**Files:**
- Create: `docs/contracts/v3/glossary.md`
- Create: `docs/contracts/v3/commands.md`

**Interfaces:**
- Consumes: Spec §2、§5
- Produces: 稳定 `command_type` 枚举与中文展示名映射，供 OpenAPI/`commands.ts` 引用

- [ ] **Step 1: 写术语表**

创建 `docs/contracts/v3/glossary.md`，至少包含：

| 用户可见 | 内部稳定 ID | 禁止对用户说 |
|----------|-------------|--------------|
| 选题定调 / 项目简报 | `project_brief` | `create-project-brief`、`operation.*` |
| 故事蓝图 | `story_bible` | `compose-story-bible` |
| 分集规划 | `episode_plan` | `design-episode-plan` |
| 剧本正文 | `episode_scripts` | `write-episodes` |
| 质量报告 | `quality_report` | `score-script` |
| 合规报告 | `compliance_report` | `check-compliance` |
| 制作交付包 | `production_package` | `prepare-delivery` |
| 运行 / 执行日志 | `command_run` | `OperationRun`（对外） |

- [ ] **Step 2: 写命令字典**

创建 `docs/contracts/v3/commands.md`：

```markdown
# V3 产品命令字典

| command_type | 中文名 | 模块 | 异步 | 需确认候选 |
|--------------|--------|------|------|------------|
| create_project | 创建项目 | 项目 | 否 | 否 |
| generate_topic_brief | 生成选题简报 | 选题 | 是 | 是 |
| confirm_topic_brief | 确认选题简报 | 选题 | 否 | 否 |
| generate_blueprint | 生成故事蓝图 | 蓝图 | 是 | 是 |
| confirm_blueprint | 确认故事蓝图 | 蓝图 | 否 | 否 |
| generate_episode_plan | 生成分集规划 | 分集 | 是 | 是 |
| revise_episode_plan | 局部修订分集 | 分集 | 是 | 是 |
| write_episode_batch | 分批写正文 | 正文 | 是 | 是 |
| confirm_script_candidate | 确认正文候选 | 正文 | 否 | 否 |
| score_quality | 质量评分 | 质检 | 是 | 否 |
| check_compliance | 合规审查 | 质检 | 是 | 否 |
| accept_findings | 接受质检问题 | 质检 | 否 | 否 |
| revise_from_findings | 按问题修订 | 质检 | 是 | 是 |
| prepare_delivery | 生成交付包 | 交付 | 是 | 否 |
| test_model_provider | 试连模型 | 模型 | 是 | 否 |
```

说明：内部 skills 配方 ID（如 `operation.create-project-brief`）只写在编排器映射表，不进本表「对用户」列。

- [ ] **Step 3: 自检**

确认表中每个 `command_type` 为 `^[a-z][a-z0-9_]*$`，且与 Spec §5 十模块覆盖无遗漏（套餐无命令、系统配置用 REST 资源而非 command）。

---

### Task 2: OpenAPI 契约（项目列表 + 命令信封）

**Files:**
- Create: `docs/contracts/v3/openapi.yaml`

**Interfaces:**
- Consumes: Task 1 命令字典
- Produces: 可被人工与测试引用的路径/Schema

- [ ] **Step 1: 创建最小 OpenAPI**

`docs/contracts/v3/openapi.yaml` 内容如下（可原样落盘，后续里程碑只追加 path，不改已有字段语义）：

```yaml
openapi: 3.0.3
info:
  title: ScriptForge Product API v3
  version: 3.0.0
servers:
  - url: /api/v3
paths:
  /projects/:
    get:
      operationId: listProjects
      summary: 项目列表
      security:
        - bearerAuth: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProjectList"
    post:
      operationId: createProject
      summary: 创建项目
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateProjectRequest"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProject"
  /projects/{project_id}/:
    get:
      operationId: getProject
      summary: 项目详情
      security:
        - bearerAuth: []
      parameters:
        - $ref: "#/components/parameters/ProjectId"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeProject"
  /billing/plans/:
    get:
      operationId: listBillingPlans
      summary: 套餐文案（只读壳）
      security:
        - bearerAuth: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeBillingPlans"
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  parameters:
    ProjectId:
      name: project_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  schemas:
    Envelope:
      type: object
      required: [code, message, data]
      properties:
        code: { type: integer }
        message: { type: string }
        data: {}
    ProjectStage:
      type: string
      enum: [topic, blueprint, episodes, writing, quality, delivery]
    ProjectSummary:
      type: object
      required: [id, title, entry_type, stage, updated_at]
      properties:
        id: { type: string, format: uuid }
        title: { type: string }
        entry_type: { type: string, enum: [original, adapt] }
        stage: { $ref: "#/components/schemas/ProjectStage" }
        progress_percent: { type: integer, minimum: 0, maximum: 100 }
        updated_at: { type: string, format: date-time }
    CreateProjectRequest:
      type: object
      required: [title, entry_type]
      properties:
        title: { type: string, minLength: 1, maxLength: 200 }
        entry_type: { type: string, enum: [original, adapt] }
    EnvelopeProjectList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data:
              type: object
              required: [items]
              properties:
                items:
                  type: array
                  items: { $ref: "#/components/schemas/ProjectSummary" }
    EnvelopeProject:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data: { $ref: "#/components/schemas/ProjectSummary" }
    BillingPlan:
      type: object
      required: [id, name, price_label, features]
      properties:
        id: { type: string }
        name: { type: string }
        price_label: { type: string }
        features:
          type: array
          items: { type: string }
    EnvelopeBillingPlans:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            data:
              type: object
              required: [items]
              properties:
                items:
                  type: array
                  items: { $ref: "#/components/schemas/BillingPlan" }
```

- [ ] **Step 2: 人工核对**

确认 path 以 `/projects/` 风格带尾斜杠（对齐 Django），与 Spec §4.1 前缀一致。

---

### Task 3: 前端 TS 类型与契约测试

**Files:**
- Create: `frontend/src/types/v3/domain.ts`
- Create: `frontend/src/types/v3/commands.ts`
- Create: `frontend/src/types/v3/api.ts`
- Create: `frontend/src/types/v3/api.test.ts`

**Interfaces:**
- Consumes: OpenAPI schemas、commands.md
- Produces: 导出类型供页面与 services 使用

- [ ] **Step 1: 写失败测试（命令枚举完整性）**

创建 `frontend/src/types/v3/api.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { PRODUCT_COMMAND_TYPES } from './commands'

describe('v3 commands contract', () => {
  it('includes generate_topic_brief and prepare_delivery', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('generate_topic_brief')
    expect(PRODUCT_COMMAND_TYPES).toContain('prepare_delivery')
    expect(PRODUCT_COMMAND_TYPES).not.toContain('create-project-brief')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npm test -- src/types/v3/api.test.ts`  
Expected: FAIL（模块不存在或 `PRODUCT_COMMAND_TYPES` 未定义）

- [ ] **Step 3: 实现类型文件**

`frontend/src/types/v3/commands.ts`：

```typescript
export const PRODUCT_COMMAND_TYPES = [
  'create_project',
  'generate_topic_brief',
  'confirm_topic_brief',
  'generate_blueprint',
  'confirm_blueprint',
  'generate_episode_plan',
  'revise_episode_plan',
  'write_episode_batch',
  'confirm_script_candidate',
  'score_quality',
  'check_compliance',
  'accept_findings',
  'revise_from_findings',
  'prepare_delivery',
  'test_model_provider',
] as const

export type ProductCommandType = (typeof PRODUCT_COMMAND_TYPES)[number]
```

`frontend/src/types/v3/domain.ts`：

```typescript
export type ProjectEntryType = 'original' | 'adapt'
export type ProjectStage = 'topic' | 'blueprint' | 'episodes' | 'writing' | 'quality' | 'delivery'

export interface ProjectSummary {
  id: string
  title: string
  entry_type: ProjectEntryType
  stage: ProjectStage
  progress_percent?: number
  updated_at: string
}

export interface CreateProjectRequest {
  title: string
  entry_type: ProjectEntryType
}

export interface BillingPlan {
  id: string
  name: string
  price_label: string
  features: string[]
}
```

`frontend/src/types/v3/api.ts`：

```typescript
export type { ProductCommandType } from './commands'
export type {
  BillingPlan,
  CreateProjectRequest,
  ProjectEntryType,
  ProjectStage,
  ProjectSummary,
} from './domain'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npm test -- src/types/v3/api.test.ts`  
Expected: PASS

---

### Task 4: 后端 `/api/v3` 空壳 + 契约冒烟测试

**Files:**
- Create: `backend/apps/drama/api/__init__.py`
- Create: `backend/apps/drama/api/v3/__init__.py`
- Create: `backend/apps/drama/api/v3/serializers.py`
- Create: `backend/apps/drama/api/v3/views.py`
- Create: `backend/apps/drama/api/v3/urls.py`
- Create: `backend/apps/drama/tests/test_v3_contract_smoke.py`
- Modify: `backend/config/urls.py`

**Interfaces:**
- Consumes: `api_response` / DRF `IsAuthenticated`
- Produces:
  - `GET /api/v3/projects/` → `{code:0, data:{items:[]}}`
  - `POST /api/v3/projects/` → 内存或最小模型创建（W0 可用临时内存列表或最小 Domain 表；优先最小 `V3Project` 模型，见 Step 3）
  - `GET /api/v3/billing/plans/` → 三档静态套餐

- [ ] **Step 1: 写失败测试**

`backend/apps/drama/tests/test_v3_contract_smoke.py`：

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class V3ContractSmokeTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="v3u", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_list_projects_envelope(self) -> None:
        resp = self.client.get("/api/v3/projects/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertIn("items", body["data"])
        self.assertIsInstance(body["data"]["items"], list)

    def test_create_project_returns_summary(self) -> None:
        resp = self.client.post(
            "/api/v3/projects/",
            {"title": "试写短剧", "entry_type": "original"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["title"], "试写短剧")
        self.assertEqual(data["entry_type"], "original")
        self.assertEqual(data["stage"], "topic")
        self.assertIn("id", data)

    def test_billing_plans_readonly_shell(self) -> None:
        resp = self.client.get("/api/v3/billing/plans/")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["data"]["items"]
        self.assertGreaterEqual(len(items), 3)
        self.assertTrue(all("price_label" in p for p in items))
```

- [ ] **Step 2: 运行测试确认失败**

Run（在 `backend` 目录，按仓库现有设置）：

```bash
cd backend
python manage.py test apps.drama.tests.test_v3_contract_smoke -v 2
```

Expected: FAIL（URL 未配置 / 404）

- [ ] **Step 3: 最小领域模型 + views**

在 `backend/apps/drama/models.py` 追加（或新建 `domain/models.py` 并在 `apps.py`/`models` 导入）：

```python
class V3Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="v3_projects")
    title = models.CharField(max_length=200)
    entry_type = models.CharField(max_length=16)  # original | adapt
    stage = models.CharField(max_length=32, default="topic")
    progress_percent = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_project"
        ordering = ["-updated_at"]
```

生成并应用迁移：

```bash
cd backend
python manage.py makemigrations drama
python manage.py migrate
```

`serializers.py`：校验 `title`、`entry_type in {original,adapt}`。  
`views.py`：列表/创建用 `api_response`；billing 返回静态三档（与 HTML 第 09 节文案对齐，可简化）。

`urls.py`：

```python
urlpatterns = [
    path("projects/", V3ProjectListCreateView.as_view()),
    path("projects/<uuid:project_id>/", V3ProjectDetailView.as_view()),
    path("billing/plans/", V3BillingPlansView.as_view()),
]
```

`backend/config/urls.py` 增加：

```python
path("api/v3/", include("apps.drama.api.v3.urls")),
```

（W0 **保留**现有 `api/v2/studio/`，删除动作留给 W6。）

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend
python manage.py test apps.drama.tests.test_v3_contract_smoke -v 2
```

Expected: PASS

---

### Task 5: 前端 App 壳与路由（替换 studio 入口）

**Files:**
- Create: `frontend/src/app/AppShell.tsx`
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/ModelsPage.tsx`
- Create: `frontend/src/pages/LogsPage.tsx`
- Create: `frontend/src/pages/SystemPage.tsx`
- Create: `frontend/src/pages/BillingPage.tsx`
- Create: `frontend/src/pages/ProjectOverviewPage.tsx`
- Create: `frontend/src/app/router.test.tsx`
- Modify: `frontend/src/App.tsx`
- Delete or stop importing: `frontend/src/studio/**` 路由引用（目录可留到 W6 物理删除，但 `App.tsx` 不得再 import studio）

**Interfaces:**
- Consumes: Spec §2 路由表、`ProtectedRoute`、`AuthProvider`
- Produces: `/dashboard`、`/models`、`/logs`、`/system`、`/billing`、`/projects/:id` 可渲染占位

- [ ] **Step 1: 写路由测试（失败）**

`frontend/src/app/router.test.tsx`：

```tsx
import { describe, expect, it } from 'vitest'
import { V3_NAV_PATHS } from './router'

describe('v3 router paths', () => {
  it('exposes product IA paths and not studio', () => {
    expect(V3_NAV_PATHS).toEqual(
      expect.arrayContaining(['/dashboard', '/models', '/logs', '/system', '/billing']),
    )
    expect(V3_NAV_PATHS.some((p) => p.startsWith('/studio'))).toBe(false)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- src/app/router.test.tsx`  
Expected: FAIL

- [ ] **Step 3: 实现壳与路由**

`router.tsx` 导出 `V3_NAV_PATHS` 与 `V3Routes` 组件；`AppShell` 侧栏五项 + 用户退出；占位页仅标题（如「创作仪表盘」）。  
`App.tsx`：`/` → Navigate `/dashboard`；登录与 ProtectedRoute 保留；**移除**全部 `/studio`、`/governance`、`/decisions`、`/runs` 路由。

- [ ] **Step 4: 测试通过 + typecheck**

```bash
cd frontend
npm test -- src/app/router.test.tsx src/types/v3/api.test.ts
npm run typecheck
```

Expected: PASS

- [ ] **Step 5: 手工冒烟（可选）**

`npm run dev`，登录后确认侧栏五项可点，无 studio 导航。

---

### Task 6: W0 验收清单

**Files:**
- Create: `docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md`

- [ ] **Step 1: 写验收记录模板并勾选**

文件内容需包含：

| 项 | 证据 | 结果 |
|----|------|------|
| glossary + commands 存在 | 路径 | ☐ |
| openapi.yaml 含 projects/billing | 路径 | ☐ |
| TS 命令枚举测试绿 | 命令输出 | ☐ |
| test_v3_contract_smoke 绿 | 命令输出 | ☐ |
| 前端无 /studio 路由 | App.tsx / router 测试 | ☐ |
| 创作者文案无 operation.* | 抽查占位页 | ☐ |

全部勾选后，W0 视为通过，方可撰写 W1 plan。

---

## Self-Review（相对 Spec）

| Spec 要求 | 本计划任务 |
|-----------|------------|
| §2 IA 路由 | Task 5 |
| §4 `/api/v3` | Task 2–4 |
| §5 命令映射起点 | Task 1 |
| §9 W0 契约 | 全文 |
| 套餐只读壳 | Task 2/4 billing |
| 不删 v2（留 W6） | Task 4 注明保留 |

无 TBD 步骤；类型名 `ProductCommandType` / `ProjectSummary` 前后一致。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md`（总览见 `2026-07-22-drama-website-v3.md`）。

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每任务新开子代理，任务间审查  
2. **Inline Execution** — 本会话按 `executing-plans` 连续执行并设检查点  

Which approach?

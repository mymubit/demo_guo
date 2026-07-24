# V3 W1 编排骨架 + 项目 CRUD + 仪表盘 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 W0 契约与空壳之上，落地可认证的编排骨架、完整项目 CRUD（含归档）、以及接真 API 的创作仪表盘，使「空项目可建、导航齐、列表可管」。

**Architecture:** 新增 `CommandRun` 与同步编排入口（`create_project` 走编排器，不直写视图）；异步命令仅登记为 `queued`/`unsupported` 桩，不调用 LLM（留给 W2）。前端新增 `services/v3`，仪表盘用 TanStack Query 拉项目列表并提供新建/进入/归档。

**Tech Stack:** Django + DRF、`api_response`、Celery（本里程碑可不投递真实 task）、React Query、现有 Button/Dialog/PageShell

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§9 W1）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W0 已通过（`docs/superpowers/baselines/2026-07-22-w0-contracts-acceptance.md`）

## Global Constraints

- 产品真相源：`drama-website-design/drama-website-design.html`
- 响应信封 `{ code, message, data }`（`apps.core.responses.api_response`）
- 创作者 UI 禁止暴露 `operation.*` / artifact key
- 本里程碑 **禁止** 调用真实 LLM / 加载 skills 配方执行（编排器只登记命令）
- 禁止往 `v2_*`、`v6_runtime`、`v6_workbench`、`v6_control_plane` 加功能
- 不引入新第三方库
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端测试优先：`py -3 manage.py test … --settings=config.settings.sqlite_test`

## File Map

| 职责 | 路径 |
|------|------|
| 领域模型 | `backend/apps/drama/models.py`（扩展 `V3Project` + 新 `V3CommandRun`）或 `domain/` 包（若拆包则本计划 tasks 内同步改 import） |
| 编排器 | `backend/apps/drama/orchestrator/__init__.py`、`dispatcher.py`、`types.py` |
| API | `backend/apps/drama/api/v3/views.py`、`serializers.py`、`urls.py` |
| 契约 | `docs/contracts/v3/openapi.yaml`、`commands.md`（归档说明） |
| 前端服务 | `frontend/src/services/v3/projects.ts` |
| 仪表盘 | `frontend/src/pages/DashboardPage.tsx`、相关组件 |
| 项目概览 | `frontend/src/pages/ProjectOverviewPage.tsx` |
| 壳打磨 | `frontend/src/app/AppShell.tsx`、`frontend/src/app/router.tsx`、`frontend/src/pages/LoginPage.tsx` |
| 测试 | `backend/apps/drama/tests/test_v3_orchestrator.py`、`test_v3_projects_crud.py`；`frontend/src/pages/DashboardPage.test.tsx`、`services/v3/projects.test.ts` |

## W1 验收标准

1. 登录用户可在仪表盘看到本人项目列表；可新建（原创/改编）；可进入 `/projects/:id`
2. 可归档项目；默认列表不显示已归档；可选「显示已归档」
3. `POST /api/v3/commands/` 接受 `create_project`（同步完成并返回 `command_run` + `project`）；未知/异步类型返回明确状态且 **不** 调 LLM
4. 项目概览展示 `stage`、`entry_type`、下一步文案（选题定调）
5. 侧栏导航与 `V3_NAV_PATHS` 单一来源；LoginPage 无 Studio/Operation 黑话
6. W0 冒烟测试仍绿；新增后端/前端测试绿

---

### Task 1: 领域扩展 — 归档字段 + CommandRun

**Files:**
- Modify: `backend/apps/drama/models.py`（`V3Project`）
- Create/Modify: migration `0013_…py`（编号以 `makemigrations` 为准）
- Test: `backend/apps/drama/tests/test_v3_projects_crud.py`（本任务先写模型相关断言，或与 Task 3 合并测 API——本任务以模型+迁移可测为准）

**Interfaces:**
- Consumes: 现有 `V3Project(id, owner, title, entry_type, stage, progress_percent, created_at, updated_at)`
- Produces:
  - `V3Project.archived_at: DateTimeField(null=True, blank=True)` — `None` 表示未归档
  - `V3CommandRun` 模型字段见下方实现

- [ ] **Step 1: 写失败测试（模型字段）**

创建 `backend/apps/drama/tests/test_v3_domain_w1.py`：

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.drama.models import V3CommandRun, V3Project


class V3DomainW1Tests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="w1u", password="pass12345")

    def test_project_can_be_archived(self) -> None:
        p = V3Project.objects.create(
            owner=self.user, title="A", entry_type="original"
        )
        self.assertIsNone(p.archived_at)
        p.archived_at = timezone.now()
        p.save(update_fields=["archived_at", "updated_at"])
        p.refresh_from_db()
        self.assertIsNotNone(p.archived_at)

    def test_command_run_defaults(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            command_type="create_project",
            status=V3CommandRun.Status.SUCCEEDED,
            request_payload={"title": "A", "entry_type": "original"},
            result_payload={},
        )
        self.assertEqual(run.command_type, "create_project")
        self.assertIsNone(run.project)
```

- [ ] **Step 2: 运行确认失败**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

Expected: FAIL（`V3CommandRun` 不存在 / `archived_at` 不存在）

- [ ] **Step 3: 实现模型**

在 `V3Project` 增加：

```python
archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
```

新增：

```python
class V3CommandRun(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "排队"
        RUNNING = "running", "执行中"
        SUCCEEDED = "succeeded", "成功"
        FAILED = "failed", "失败"
        UNSUPPORTED = "unsupported", "本阶段未实现"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="v3_command_runs")
    project = models.ForeignKey(
        V3Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="command_runs"
    )
    command_type = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    idempotency_key = models.CharField(max_length=64, blank=True, default="")
    request_payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_command_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["command_type", "status"]),
        ]
```

然后：

```bash
py -3 manage.py makemigrations drama
py -3 manage.py migrate
```

注意：若 `makemigrations` 再次夹带无关 `RenameIndex`，**拆成仅含本任务字段的迁移**或在报告中标明并尽量避免。

- [ ] **Step 4: 测试通过**

同上 test 命令 → Expected: PASS

---

### Task 2: 编排器骨架（同步 create_project + 异步桩）

**Files:**
- Create: `backend/apps/drama/orchestrator/types.py`
- Create: `backend/apps/drama/orchestrator/dispatcher.py`
- Create: `backend/apps/drama/orchestrator/__init__.py`
- Test: `backend/apps/drama/tests/test_v3_orchestrator.py`

**Interfaces:**
- Consumes: `V3Project`, `V3CommandRun`, `PRODUCT` command types from `docs/contracts/v3/commands.md`
- Produces:
  - `dispatch_command(*, owner, command_type: str, payload: dict, idempotency_key: str = "") -> V3CommandRun`
  - 同步：`create_project` → 创建项目，`status=succeeded`，`result_payload={"project_id": "..."}`，`project` FK 已设
  - 异步白名单（W2+）：`generate_topic_brief` 等 → `status=unsupported`，`error_message` 含人话「将在后续里程碑开放」，**不** import skills / LLM
  - 未知 `command_type` → `status=failed`，`error_message` 说明非法命令

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command


class V3OrchestratorTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="orch", password="pass12345")

    def test_create_project_succeeds_sync(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload={"title": "新剧", "entry_type": "adapt"},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertIsNotNone(run.project_id)
        project = V3Project.objects.get(id=run.project_id)
        self.assertEqual(project.title, "新剧")
        self.assertEqual(project.entry_type, "adapt")
        self.assertEqual(project.stage, "topic")
        self.assertEqual(str(run.result_payload.get("project_id")), str(project.id))

    def test_async_command_is_unsupported_stub(self) -> None:
        project = V3Project.objects.create(owner=self.user, title="P", entry_type="original")
        run = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(project.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.UNSUPPORTED)
        self.assertIn("后续", run.error_message)

    def test_unknown_command_fails(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create-project-brief",
            payload={},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
```

- [ ] **Step 2: 运行确认失败**

```bash
py -3 manage.py test apps.drama.tests.test_v3_orchestrator -v 2 --settings=config.settings.sqlite_test
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 dispatcher**

`types.py`：定义 `SYNC_COMMANDS = frozenset({"create_project"})` 与 `ASYNC_STUB_COMMANDS`（commands.md 中除 `create_project` 外全部）。

`dispatcher.py` 核心逻辑（示意）：

```python
def dispatch_command(*, owner, command_type: str, payload: dict, idempotency_key: str = "") -> V3CommandRun:
    run = V3CommandRun.objects.create(
        owner=owner,
        command_type=command_type,
        status=V3CommandRun.Status.RUNNING,
        idempotency_key=idempotency_key or "",
        request_payload=payload or {},
    )
    if command_type == "create_project":
        title = (payload or {}).get("title") or ""
        entry_type = (payload or {}).get("entry_type") or ""
        if not title or entry_type not in ("original", "adapt"):
            run.status = V3CommandRun.Status.FAILED
            run.error_message = "标题与创作来源（原创/改编）不能为空"
            run.save(update_fields=["status", "error_message", "updated_at"])
            return run
        project = V3Project.objects.create(
            owner=owner, title=title[:200], entry_type=entry_type, stage=V3Project.Stage.TOPIC
        )
        run.project = project
        run.status = V3CommandRun.Status.SUCCEEDED
        run.result_payload = {"project_id": str(project.id)}
        run.save(update_fields=["project", "status", "result_payload", "updated_at"])
        return run
    if command_type in ASYNC_STUB_COMMANDS:
        run.status = V3CommandRun.Status.UNSUPPORTED
        run.error_message = "该创作命令将在后续里程碑开放，当前仅完成项目与仪表盘"
        run.save(update_fields=["status", "error_message", "updated_at"])
        return run
    run.status = V3CommandRun.Status.FAILED
    run.error_message = "未知命令"
    run.save(update_fields=["status", "error_message", "updated_at"])
    return run
```

`__init__.py`：`from .dispatcher import dispatch_command`

- [ ] **Step 4: 测试通过**

同上 → PASS

---

### Task 3: `/api/v3` 项目 CRUD + commands 端点

**Files:**
- Modify: `backend/apps/drama/api/v3/serializers.py`
- Modify: `backend/apps/drama/api/v3/views.py`
- Modify: `backend/apps/drama/api/v3/urls.py`
- Modify: `docs/contracts/v3/openapi.yaml`（追加 archive、commands）
- Test: `backend/apps/drama/tests/test_v3_projects_crud.py`
- Modify: 可选让 `V3ProjectListCreateView.post` 改为调用 `dispatch_command`（保持 OpenAPI 200 行为）

**Interfaces:**
- Consumes: `dispatch_command`、`V3Project`、`V3CommandRun`
- Produces HTTP:
  - `GET /api/v3/projects/?include_archived=0|1` — 默认仅 `archived_at ISNULL`
  - `POST /api/v3/projects/` — 内部 `dispatch_command(create_project)`，仍返回 `ProjectSummary`（兼容 W0）
  - `POST /api/v3/projects/{id}/archive/` — 设 `archived_at=now()`，幂等
  - `POST /api/v3/commands/` body `{command_type, payload, idempotency_key?}` → `{command_run: {...}, project?: summary}`
  - `GET /api/v3/commands/{run_id}/` — 本人运行详情

`CommandRun` 序列化字段：`id, command_type, status, project_id, error_message, result_payload, created_at, updated_at`

- [ ] **Step 1: 写 API 失败测试**

```python
# 关键用例（APITestCase + force_authenticate）
# 1) create via POST /projects/ → 200 + stage topic
# 2) list excludes archived by default
# 3) archive then list empty; include_archived=1 可见
# 4) POST /commands/ create_project → succeeded + project
# 5) POST /commands/ generate_topic_brief → unsupported
# 6) 他用户 project 404 on archive
```

完整测试文件按上列用例编写（每用例独立方法）。

- [ ] **Step 2: 运行确认至少部分失败**

```bash
py -3 manage.py test apps.drama.tests.test_v3_projects_crud -v 2 --settings=config.settings.sqlite_test
```

- [ ] **Step 3: 实现 serializers/views/urls + 更新 openapi.yaml**

`urls.py` 追加：

```python
path("projects/<uuid:project_id>/archive/", V3ProjectArchiveView.as_view()),
path("commands/", V3CommandDispatchView.as_view()),
path("commands/<uuid:run_id>/", V3CommandRunDetailView.as_view()),
```

列表 GET 读取 `include_archived` query（`"1"`/`"true"` 为真）。

- [ ] **Step 4: 全绿 + 回归 W0 冒烟**

```bash
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_domain_w1 -v 2 --settings=config.settings.sqlite_test
```

Expected: 全部 PASS

---

### Task 4: 前端 v3 projects 客户端 + 类型补全

**Files:**
- Create: `frontend/src/services/v3/projects.ts`
- Create: `frontend/src/services/v3/projects.test.ts`
- Modify: `frontend/src/types/v3/domain.ts`（`archived_at?: string | null`；`CommandRunSummary`）
- Modify: `frontend/src/types/v3/api.ts`（导出）

**Interfaces:**
- Consumes: `http` 模块现有 `get/post`（查看 `frontend/src/services/http.ts` 导出的请求函数名，按仓库实际使用；若仅 axios 封装则用同一套）
- Produces:
  - `listProjects(includeArchived?: boolean): Promise<ProjectSummary[]>`
  - `createProject(body: CreateProjectRequest): Promise<ProjectSummary>`
  - `getProject(id: string): Promise<ProjectSummary>`
  - `archiveProject(id: string): Promise<ProjectSummary>`
  - `dispatchCommand(input: { command_type: string; payload: Record<string, unknown>; idempotency_key?: string }): Promise<{ command_run: CommandRunSummary; project?: ProjectSummary }>`

- [ ] **Step 1: 读 `http.ts` 确认导出 API（`request` / `http.get` 等），按现有模式写 clients**

- [ ] **Step 2: 写 `projects.test.ts`**（用 vitest mock axios/http），至少覆盖：
  - `listProjects` 请求 `/api/v3/projects/` 且默认无 `include_archived`
  - `archiveProject` POST `/api/v3/projects/{id}/archive/`

- [ ] **Step 3: 实现并跑通**

```bash
cd frontend
npm test -- src/services/v3/projects.test.ts src/types/v3/api.test.ts
```

Expected: PASS

---

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

### Task 7: W0 Minor 打磨 — 导航单一来源 + Login 文案

**Files:**
- Modify: `frontend/src/app/router.tsx`、`AppShell.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/app/router.test.tsx`（若需要）

**Interfaces:**
- Consumes: `V3_NAV_PATHS`
- Produces: `AppShell` 从单一 `V3_NAV_ITEMS`（path+label+hint+icon）导出；`V3_NAV_PATHS = V3_NAV_ITEMS.map(i => i.to)`；LoginPage 中文产品名「短剧剧本创作一体机」或「ScriptForge」，删除 Operation graph / Studio V6 旁白

- [ ] **Step 1: 改 LoginPage 文案并目视确认无 `operation`/`Studio V6` 字符串**（可加简单测试 `expect(source).not.toMatch(/Operation graph/)`）

- [ ] **Step 2: 统一导航常量**

- [ ] **Step 3:**

```bash
cd frontend
npm test -- src/app/router.test.tsx
npm run typecheck
```

---

### Task 8: W1 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W1 行改为指向本 plan）

- [ ] **Step 1: 按「W1 验收标准」逐条勾选并写证据命令/路径**

- [ ] **Step 2: 回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud -v 1 --settings=config.settings.sqlite_test
cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx
npm run typecheck
```

全部绿且验收表勾完 → W1 通过，方可写 W2 plan。

---

## Self-Review

| Spec / Roadmap W1 | 任务 |
|-------------------|------|
| 编排骨架 | Task 2–3 |
| 项目 CRUD + 归档 | Task 1, 3, 5–6 |
| 仪表盘可用 | Task 5 |
| 导航齐 | Task 6–7 |
| 不调 LLM | Task 2 约束 |
| W0 Minor | Task 7 |

无 TBD 步骤；`dispatch_command` / `V3CommandRun` / `archived_at` 命名前后一致。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-23-drama-website-v3-w1-shell-projects.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每任务新开子代理 + 任务间审查  
2. **Inline Execution** — 本会话连续执行并设检查点  

Which approach?

# V3 W2 选题 + 蓝图（真实 LLM 编排）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通「选题定调 → 确认简报 → 生成蓝图组 → 确认蓝图」主链前半：异步命令真实调用 drama-skills 配方 + LLM，候选产物可预览/确认提交，项目阶段前进。

**Architecture:** 扩展 W1 `dispatch_command`：W2 命令入队 Celery → `skills_bridge` 加载配方/拼 prompt/调现有 `LlmProvider` → schema 校验 → 写入 `V3ArtifactVersion(status=candidate)`；`confirm_*` 同步将候选升为 `committed` 并更新 `V3Project.stage`。禁止调用 `v6_runtime` / `v6_workbench` / `v6_control_plane`。

**Tech Stack:** Django、DRF、Celery、`skills_loader`、`LlmProvider`、现有 schema JSON、React Query、Vitest、Django TestCase（LLM **必须 mock**）

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§3–5 选题/蓝图）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W1 已通过（`docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md`）

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / `create-project-brief` 等配方 ID（日志高级态除外，本里程碑日志页可仍占位）
- **禁止** import 或调用 `apps.drama.services.v6_runtime` / `v6_workbench` / `v6_control_plane`
- 可复用：`skills_loader`、`llm_provider`、`secret_crypto`、schema 文件；**不要**走旧 `GenerationService` / `DramaGenerationJob` 主路径
- 单元/API 测试必须 mock LLM（禁止依赖外网）
- 不引入新第三方库
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端测试：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- Celery 测试：`CELERY_TASK_ALWAYS_EAGER=True`（在测试 settings 或 `@override_settings`）

## File Map

| 职责 | 路径 |
|------|------|
| 产物版本 | `backend/apps/drama/models.py` → `V3ArtifactVersion` |
| 配方映射 | `backend/apps/drama/skills_bridge/recipe_map.py` |
| Prompt/调用 | `backend/apps/drama/skills_bridge/executor.py` |
| 校验 | `backend/apps/drama/skills_bridge/validate.py` |
| 编排扩展 | `backend/apps/drama/orchestrator/dispatcher.py`、`types.py`、`async_runner.py` |
| Celery | `backend/apps/drama/tasks_v3.py`（新建，避免搅乱旧 `tasks.py`） |
| API | `backend/apps/drama/api/v3/topic.py`、`blueprint.py`、urls/serializers |
| 契约 | `docs/contracts/v3/openapi.yaml`、可选补充 `artifacts.md` |
| 前端 | `frontend/src/projects/TopicPage.tsx`、`BlueprintPage.tsx`、`services/v3/topic.ts`、`blueprint.ts` |
| 路由 | `frontend/src/app/router.tsx`（替换占位 Topic；新增 blueprint） |
| 测试 | `test_v3_artifact.py`、`test_v3_skills_bridge.py`、`test_v3_topic_api.py`、`test_v3_blueprint_api.py`；前端对应 `*.test.tsx` |
| Fixture | `backend/apps/drama/tests/fixtures/v3_project_brief_candidate.json`、`v3_blueprint_bundle.json` |

## W2 命令语义

| command_type | 模式 | 行为 |
|--------------|------|------|
| `generate_topic_brief` | 异步 | 读项目输入 → LLM → 候选 `project_brief` |
| `confirm_topic_brief` | 同步 | 指定候选 version → `committed`；`stage=blueprint`（若仍为 topic） |
| `generate_blueprint` | 异步 | 依赖已确认 `project_brief` → 一次运行写出多产物候选：`story_bible`、`character_system`、`world_system`、`emotion_system`、`originality_report`（同一 `command_run_id`） |
| `confirm_blueprint` | 同步 | 将上述五产物同批候选升为 committed；`stage=episodes` |

人工编辑：`PUT/PATCH .../topic/`、`.../blueprint/` 写 **draft**（`V3ArtifactDraft` 或 `status=draft` 行），确认时可选择「以草稿为准」或「以候选为准」——W2 **最小实现**：确认只提交当前 `candidate`；草稿保存单独 API，确认前若存在更新的 draft 则 `confirm` 将 draft 内容写入新 committed（见 Task 5）。

## W2 验收标准

1. 对已建项目可触发「生成选题简报」，命令 `queued→running→succeeded`，出现 `project_brief` 候选
2. 可确认简报；确认后 `stage=blueprint`，存在 `committed` 简报
3. 可触发「生成蓝图」；五产物均有候选且绑定同一 `command_run`
4. 可确认蓝图；`stage=episodes`；五产物 committed
5. UI：Topic / Blueprint 页无 operation ID；可看到候选人话摘要与确认/重新生成
6. 全套测 LLM 为 mock；W0/W1 回归仍绿
7. 无 `v6_runtime` 引用出现在新增代码中（可用 grep 验收）

---

### Task 1: `V3ArtifactVersion` + 可选 Draft

**Files:**
- Modify: `backend/apps/drama/models.py`
- Create: migration `0014_…`
- Test: `backend/apps/drama/tests/test_v3_artifact.py`

**Interfaces:**
- Produces model:

```python
class V3ArtifactVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        CANDIDATE = "candidate", "候选"
        COMMITTED = "committed", "已确认"
        SUPERSEDED = "superseded", "已替代"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(V3Project, on_delete=models.CASCADE, related_name="artifacts")
    artifact_key = models.CharField(max_length=64)  # project_brief, story_bible, ...
    version = models.PositiveIntegerField()
    schema_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices)
    payload = models.JSONField(default=dict)
    command_run = models.ForeignKey(
        V3CommandRun, null=True, blank=True, on_delete=models.SET_NULL, related_name="artifacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_artifact_version"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "artifact_key", "version"],
                name="uniq_v3_artifact_version",
            ),
        ]
```

Helper（可放 `orchestrator/artifacts.py` 或 model 方法）：

```python
def next_version(project_id, artifact_key) -> int: ...
def latest(project, artifact_key, status=None) -> V3ArtifactVersion | None: ...
```

- [ ] **Step 1: 写失败测试** — 创建 candidate、unique (project,key,version)

- [ ] **Step 2: 跑测 FAIL**

```bash
py -3 manage.py test apps.drama.tests.test_v3_artifact -v 2 --settings=config.settings.sqlite_test
```

- [ ] **Step 3: 模型 + migrate**

- [ ] **Step 4: 测 PASS**

---

### Task 2: `skills_bridge` 配方映射 + 校验（无 LLM）

**Files:**
- Create: `backend/apps/drama/skills_bridge/__init__.py`
- Create: `backend/apps/drama/skills_bridge/recipe_map.py`
- Create: `backend/apps/drama/skills_bridge/validate.py`
- Test: `backend/apps/drama/tests/test_v3_skills_bridge.py`
- Fixture: `backend/apps/drama/tests/fixtures/v3_project_brief_candidate.json`（从 `drama-skills/schemas/artifacts/project_brief/1.schema.json` 构造最小合法样例；可先用精简必填字段）

**Interfaces:**
- Produces:

```python
# recipe_map.py
COMMAND_RECIPES: dict[str, dict] = {
  "generate_topic_brief": {
    "recipe_id": "create-project-brief",  # 内部 only
    "role": "drama-topic-director",
    "writes": ["project_brief"],
  },
  "generate_blueprint": {
    "recipe_id": "compose-story-bible",
    "role": "drama-story-bible",
    "writes": [
      "story_bible", "character_system", "world_system",
      "emotion_system", "originality_report",
    ],
  },
}

def recipe_for(command_type: str) -> dict: ...
```

```python
# validate.py
def validate_artifact_payload(artifact_key: str, payload: dict) -> list[str]:
    """返回错误列表；空列表表示通过。优先用 skills_loader / jsonschema 对齐仓库现有校验方式。"""
```

- [ ] **Step 1: 测试** — `recipe_for("generate_topic_brief")["writes"] == ["project_brief"]`；非法 payload 返回非空错误；fixture 合法 payload 通过

- [ ] **Step 2–4: TDD 实现至 PASS** — 实现时阅读 `apps.drama.services.skills_loader` 现有 API，**不要**新造第二套 schema 路径

---

### Task 3: LLM executor（可注入 mock）

**Files:**
- Create: `backend/apps/drama/skills_bridge/executor.py`
- Extend tests in `test_v3_skills_bridge.py`

**Interfaces:**
- Produces:

```python
def execute_generation(
    *,
    command_type: str,
    project: V3Project,
    run: V3CommandRun,
    llm_call: Callable[..., str] | None = None,
) -> list[V3ArtifactVersion]:
    """
    1) recipe_for(command_type)
    2) 组装最小 user/system 上下文（项目 title/entry_type + 已 committed 依赖产物）
    3) llm_call(prompt) -> JSON text；默认实现走 LlmProvider（读激活供应商）
    4) 解析 JSON；按 writes 拆分或整包映射
    5) validate；失败 raise GenerationError
    6) 为每个 write 创建 V3ArtifactVersion(status=candidate, command_run=run)
    返回创建的候选列表
    """
```

**generate_topic_brief 输出约定（测试用）：** LLM 返回单个 JSON 对象 = `project_brief` payload。  
**generate_blueprint 输出约定：** LLM 返回：

```json
{
  "story_bible": {},
  "character_system": {},
  "world_system": {},
  "emotion_system": {},
  "originality_report": {}
}
```

- [ ] **Step 1: 测试用 fake `llm_call` 返回 fixture** — 断言写出 1 或 5 条 candidate，且 `validate` 通过

- [ ] **Step 2: FAIL → 实现 → PASS**

- [ ] **Step 3: 默认 `llm_call` 路径** — 若无激活 Provider，抛出人话错误「请先在模型配置中配置并启用供应商」（W5 前可在测试中不覆盖默认路径，或 mock Provider）

**注意：** Prompt 拼装可极简（角色 SKILL.md 前 N 字 + 用户输入 JSON）；W2 不追求 injection 完整度，但必须从 `drama-skills/roles/.../SKILL.md` 或 role.yaml 读取，禁止硬编码整份技能正文在 Python 里。

---

### Task 4: 异步编排 + Celery 任务

**Files:**
- Modify: `backend/apps/drama/orchestrator/types.py` — 从 `ASYNC_STUB_COMMANDS` 移除四条 W2 命令；新增 `ASYNC_LIVE_COMMANDS`、`SYNC_CONFIRM_COMMANDS`
- Modify: `backend/apps/drama/orchestrator/dispatcher.py`
- Create: `backend/apps/drama/orchestrator/async_runner.py`
- Create: `backend/apps/drama/tasks_v3.py`
- Create: `backend/apps/drama/orchestrator/confirm.py`
- Test: `backend/apps/drama/tests/test_v3_async_commands.py`

**Interfaces:**
- `dispatch_command` 对 `generate_topic_brief` / `generate_blueprint`：
  1. 校验 `payload.project_id` 且项目属主
  2. 创建 run `queued`，绑定 project
  3. 调用 `enqueue_v3_command(run.id)` → Celery
  4. 立即返回 run（status=`queued`）
- `run_v3_command_task(run_id)`：
  1. 置 `running`
  2. `execute_generation(...)`
  3. `succeeded` + `result_payload={artifact_ids:[...]}`；失败则 `failed` + `error_message` 人话
- `confirm_topic_brief` / `confirm_blueprint`：**同步**，实现于 `confirm.py`：
  - payload: `{project_id, artifact_version_ids?: []}`；默认取各 key 最新 candidate
  - 将 candidate → committed；同 key 旧 committed → superseded
  - 更新 stage（topic→blueprint / blueprint→episodes）
  - 蓝图确认必须五产物齐全，否则 failed

- [ ] **Step 1: 测试（ALWAYS_EAGER + mock llm_call 注入点）**

注入策略：在 `async_runner` 读取 `settings.V3_LLM_CALL_OVERRIDE` 可调用对象（仅测试 settings 设置），生产为 `None`。

用例：
1. generate_topic_brief → eager 后 succeeded + 1 candidate
2. confirm_topic_brief → committed + stage blueprint
3. generate_blueprint 无 brief → failed 人话
4. generate_blueprint 有 brief → 5 candidates
5. confirm_blueprint → stage episodes
6. grep 保障：`orchestrator`/`skills_bridge`/`tasks_v3` 文件文本不含 `v6_runtime`

- [ ] **Step 2–4: 实现至 PASS**；更新 `_UNSUPPORTED_MESSAGE` 仅对仍 stub 的命令

---

### Task 5: Topic / Blueprint REST API

**Files:**
- Create: `backend/apps/drama/api/v3/topic_views.py`、`blueprint_views.py`（或合并 `artifacts_views.py`）
- Modify: `serializers.py`、`urls.py`
- Modify: `docs/contracts/v3/openapi.yaml`
- Test: `test_v3_topic_api.py`、`test_v3_blueprint_api.py`

**Interfaces（均需登录 + owner）：**

```
GET  /api/v3/projects/{id}/topic/
  → { stage, committed: ProjectBrief|null, candidate: ProjectBrief|null, draft: ...|null, latest_run: CommandRunSummary|null }

PUT  /api/v3/projects/{id}/topic/draft/
  body: { payload: object } → draft artifact

POST /api/v3/projects/{id}/topic/generate/
  → 等价 dispatch generate_topic_brief（可内部调 dispatch_command）

POST /api/v3/projects/{id}/topic/confirm/
  body: { use_draft?: bool } → confirm_topic_brief

GET  /api/v3/projects/{id}/blueprint/
  → { committed: {story_bible, ...}|null, candidate: {...}|null, latest_run }

POST /api/v3/projects/{id}/blueprint/generate/
POST /api/v3/projects/{id}/blueprint/confirm/
```

响应字段用业务名；可附 `artifact_key` 给前端映射，但 UI 文案仍用中文。

- [ ] **Step 1: API 测试（eager + mock）覆盖 generate→get 见 candidate→confirm→get 见 committed**

- [ ] **Step 2–4: 实现 + OpenAPI 更新 + PASS**；回归 W1 CRUD 测试

---

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

### Task 7: 前端 Blueprint 页

**Files:**
- Create: `frontend/src/pages/BlueprintPage.tsx`、`services/v3/blueprint.ts`、测试
- Modify: `router.tsx` — `/projects/:id/blueprint`
- Modify: `ProjectOverviewPage` — stage 为 blueprint 时 CTA「去故事蓝图」

**UI：**
- Tab 或分段：故事蓝图 / 人物 / 世界 / 情绪 / 原创性（中文）
- 生成 / 确认 / 依赖提示（无已确认简报时禁用生成并说明）
- 轮询 run 状态

- [ ] **Step 1–4: TDD + 实现 + typecheck**

---

### Task 8: 幂等键 + 概览小修（W1 Minor）

**Files:**
- Modify: `dispatcher.py` — 若 `idempotency_key` 非空且同 owner+key 已有成功/进行中 run，返回已有 run（不新建）
- Modify: `ProjectOverviewPage.tsx` — 已归档隐藏归档按钮
- Migration：可选 `UniqueConstraint(owner, idempotency_key)` where key != ''（若 DB 支持；SQLite 测试可用）

- [ ] **Step 1: 测试重复 idempotency_key 不双建项目/双候选**

- [ ] **Step 2–4: 实现 PASS**

---

### Task 9: W2 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w2-topic-blueprint-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W2 行指向本 plan）

- [ ] **Step 1: 跑回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api -v 1 --settings=config.settings.sqlite_test

cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx src/pages/TopicPage.test.tsx src/pages/BlueprintPage.test.tsx
npm run typecheck
```

- [ ] **Step 2: grep 验收**

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

Expected: 无匹配

- [ ] **Step 3: 勾选验收表；全部通过才可写 W3 plan**

---

## Self-Review

| Spec 要求 | 任务 |
|-----------|------|
| 选题 generate/confirm | Task 3–6 |
| 蓝图多产物原子候选/确认 | Task 3–5, 7 |
| 真实 skills+LLM（可 mock） | Task 2–4 |
| 不暴露 operation ID | Task 6–7 |
| 不用 v6_runtime | Task 4/9 grep |
| 阶段推进 | Task 4 confirm |

无 TBD；`execute_generation` / `V3ArtifactVersion` / `ASYNC_LIVE_COMMANDS` 命名前后一致。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-23-drama-website-v3-w2-topic-blueprint.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）**
2. **Inline Execution**

Which approach?

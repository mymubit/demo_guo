# V3 P2-W1 Failover 运行时 + Logs 尝试展示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地跨供应商主备链解析、可审计 `V3FailoverAttempt`、生成路径经 `LlmRouter` 自动 failover，并在 Logs run 详情展示尝试列表；试连仍只测指定 provider。

**Architecture:** 扩展 `V3RoleModelMapping.backup_provider_ids`；新增 `V3FailoverAttempt`；`failover_policy` 判定可切换错误并解析链；`llm_router` 按链调用 `LlmProvider` 并写 attempt + 关联 call log；`skills_bridge/executor._default_llm_call` 改走 router；Logs API/UI 挂载 attempts。单价/rollup/`/usage`/ECharts **不在本里程碑**。

**Tech Stack:** Django + DRF + 现有 `LlmProvider` / `LlmConfigService`；React LogsPage；无新第三方库。

**Spec:** `docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`（§3–5、§6 Logs、§8.2 项 1/2/5）  
**Roadmap:** `docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`  
**Prerequisite:** phase-1 W6 已通过

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / 配方 ID
- 禁止 `v6_runtime` / `v6_workbench` / `v6_control_plane`；禁止往 `v2_*` 加功能
- 单元测试 mock LLM HTTP；禁止外网
- **不**引入 ECharts / 单价表 / Usage API（属 W2/W3）
- `test_model_provider` **不走**备选链
- Commit 步骤默认 **跳过**（除非用户明确要求）
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- `DRAMA_SKILLS_ROOT` → `c:\Users\99193\Desktop\demo_guo\drama-skills`

## File Map

| 职责 | 路径 |
|------|------|
| 映射备选字段 + Attempt 模型 | `backend/apps/drama/models.py` + migration `0020_…` |
| 策略 | `backend/apps/drama/orchestrator/failover_policy.py` |
| 路由调用 | `backend/apps/drama/orchestrator/llm_router.py` |
| 生成接入 | `backend/apps/drama/skills_bridge/executor.py` |
| Logs 序列化 | `backend/apps/drama/api/v3/logs_views.py`（及 serializer 若有） |
| OpenAPI / TS | `docs/contracts/v3/openapi.yaml`、`frontend/src/types/v3/domain.ts` |
| Models API 最小暴露备选 | `api/v3/models_service.py`、`serializers.py`（读/写字段，完整 UI 在 W2） |
| 前端 Logs | `frontend/src/pages/LogsPage.tsx` + test |
| 测试 | `test_v3_failover_policy.py`、`test_v3_llm_router.py`、`test_v3_failover_executor.py`、`test_v3_logs_api.py` 扩展 |

---

### Task 1: 数据模型 — backup_provider_ids + V3FailoverAttempt

**Files:**
- Modify: `backend/apps/drama/models.py`
- Create: `backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py`
- Test: `backend/apps/drama/tests/test_v3_failover_models.py`

**Interfaces:**
- Produces: `V3RoleModelMapping.backup_provider_ids: list`（JSONField default `list`）
- Produces: model `V3FailoverAttempt` with fields per Spec §4.2；`Status` TextChoices: `succeeded` | `failed_switchable` | `failed_terminal` | `skipped`
- Consumes: existing `DramaLlmProvider`, `V3CommandRun`, `V3Project`, `DramaLlmCallLog`, `AUTH_USER_MODEL`

- [ ] **Step 1: Write the failing test**

```python
# test_v3_failover_models.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.drama.models import (
    DramaLlmProvider,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)

class FailoverModelTests(TestCase):
    def test_mapping_backup_ids_default_empty_and_attempt_create(self):
        user = get_user_model().objects.create_user("m1", password="x")
        p1 = DramaLlmProvider.objects.create(
            name="A", base_url="https://a.example", model_name="m",
            api_key_encrypted="x", is_enabled=True,
        )
        mapping = V3RoleModelMapping.objects.create(
            role_key="drama-script-writer", provider=p1
        )
        self.assertEqual(mapping.backup_provider_ids, [])
        project = V3Project.objects.create(
            owner=user, title="t", entry_type="original", stage="topic"
        )
        attempt = V3FailoverAttempt.objects.create(
            owner=user,
            v3_project=project,
            role_key="drama-script-writer",
            provider=p1,
            attempt_index=0,
            status=V3FailoverAttempt.Status.SUCCEEDED,
        )
        self.assertEqual(attempt.status, "succeeded")
```

（若 `DramaLlmProvider` 构造字段与仓库不一致，按现有 `test_v3_models_api` 的 create 方式对齐。）

- [ ] **Step 2: Run test to verify it fails**

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models --settings=config.settings.sqlite_test -v 1
```

Expected: FAIL（模型/字段不存在）

- [ ] **Step 3: Write minimal implementation**

在 `models.py`：

1. `V3RoleModelMapping` 增加：
```python
backup_provider_ids = models.JSONField(default=list, blank=True)
```

2. 新增 `V3FailoverAttempt`（`db_table = "drama_v3_failover_attempt"`），字段对齐 Spec §4.2；索引：`v3_command_run`, `-created_at`。

3. `makemigrations` → `0020_…`（名称可微调，但必须可 apply）。

- [ ] **Step 4: Run test to verify it passes**

同 Step 2；Expected: OK

- [ ] **Step 5: Commit** — 跳过（除非用户要求）

---

### Task 2: failover_policy — 链解析 + 错误可切换判定

**Files:**
- Create: `backend/apps/drama/orchestrator/failover_policy.py`
- Test: `backend/apps/drama/tests/test_v3_failover_policy.py`

**Interfaces:**
- Consumes: `V3RoleModelMapping`, `DramaLlmProvider`, `LlmConfigService.resolve_for_role` / provider 行
- Produces:
```python
@dataclass(frozen=True)
class ProviderHop:
    provider_id: str
    provider_name: str
    config: ResolvedLlmConfig  # 已有类型
    attempt_index: int

def resolve_chain(role_key: str) -> list[ProviderHop]:
    """主 provider + backup_provider_ids 去重保序；跳过不存在 id；空映射则单跳 active/resolve。"""

def classify_provider_error(exc: BaseException) -> tuple[str, bool]:
    """返回 (error_code, is_switchable)。
    可切换：timeout/连接、HTTP 401/403/408/429/5xx、未启用/配置不全。
    不可切换：其它（默认 False，避免吞业务错）。
    """
```

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_chain_primary_then_backups_deduped(self):
    # 建 p1,p2,p3；mapping.provider=p1, backup=[p2.id, p1.id, p3.id]
    # hops = resolve_chain("drama-script-writer")
    # ids == [p1, p2, p3]  # 主不重复

def test_classify_timeout_switchable(self):
    code, ok = classify_provider_error(TimeoutError("x"))
    assert ok and code == "timeout"

def test_classify_generic_not_switchable(self):
    code, ok = classify_provider_error(ValueError("bad json later"))
    assert not ok
```

对 `LlmProviderError`：解析 message / 可选挂 `http_status` 属性（若现有异常无 status，用消息子串 `HTTP 429` 等匹配，与 `llm_provider.py` 抛错文案对齐）。

- [ ] **Step 2: Run — expect FAIL**

```powershell
py -3 manage.py test apps.drama.tests.test_v3_failover_policy --settings=config.settings.sqlite_test -v 1
```

- [ ] **Step 3: Implement `failover_policy.py`**

- `resolve_chain`：若存在 mapping → 主 + backups；每跳用该 provider 构建 `ResolvedLlmConfig`（复用 `LlmConfigService` 已有从 provider 构造逻辑；必要时抽小函数 `_config_from_provider(provider, temperature=, max_tokens=)`）。
- 无 mapping：单元素链，等价今日 `resolve()` / `resolve_for_role` 行为。
- `classify_provider_error`：按 Spec §5。

- [ ] **Step 4: Run — expect OK**

- [ ] **Step 5: Commit** — 跳过

---

### Task 3: llm_router — 按链调用并写 FailoverAttempt

**Files:**
- Create: `backend/apps/drama/orchestrator/llm_router.py`
- Test: `backend/apps/drama/tests/test_v3_llm_router.py`

**Interfaces:**
- Consumes: `resolve_chain`, `classify_provider_error`, `LlmProvider.chat_completion`, `V3FailoverAttempt`
- Produces:
```python
def chat_with_failover(
    *,
    role_key: str,
    system_prompt: str,
    user_prompt: str,
    owner,
    v3_command_run=None,
    v3_project=None,
    json_mode: bool = True,
    chat_fn=None,  # 可注入，默认 LlmProvider.chat_completion
) -> dict:
    """返回与 LlmProvider.chat_completion 相同结构的 response dict。
    链耗尽时 raise LlmProviderError，message 含中文「已尝试供应商」与名称列表。
    """
```

每次 attempt：
1. `V3FailoverAttempt.objects.create(..., status` 可先 succeeded 路径直接写终态，或 create 后 update）
2. 调用 `chat_fn(..., config=hop.config)`
3. 成功：attempt=`succeeded`，若有 call log 关联则挂 FK（若 call log 由外层 `llm_call_scope` 写，router 内用 `DramaLlmCallLog.objects.filter(v3_command_run=...).order_by('-created_at').first()` 弱关联；**或** chat_fn 包装层返回 log id——优先：在已有 `llm_call_scope` 下调用，attempt 完成后绑定最新一条同 run 的 log）
4. 失败 + switchable：`failed_switchable`，继续
5. 失败 + not switchable：`failed_terminal`，raise
6. 耗尽：raise

- [ ] **Step 1: Write the failing test**

```python
@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class LlmRouterTests(TestCase):
    def test_failover_to_backup_on_switchable_error(self):
        # mapping 主=p1 备=p2；chat_fn 第一次 raise LlmProviderError("LLM HTTP 503")，第二次返回假 choices
        # resp = chat_with_failover(...)
        # attempts.count()==2；statuses == failed_switchable, succeeded

    def test_exhausted_chain_raises_with_zh_summary(self):
        # 两跳均 503；assertRaises；str(exc) 含「已尝试供应商」

    def test_terminal_error_stops_without_backup(self):
        # 第一跳 raise ValueError 或 classify 为不可切换的 LlmProviderError 文案
        # attempts==1 failed_terminal；不调用第二跳
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `llm_router.py`**

- [ ] **Step 4: Run — expect OK**

- [ ] **Step 5: Commit** — 跳过

---

### Task 4: executor 接入 router；试连不走链

**Files:**
- Modify: `backend/apps/drama/skills_bridge/executor.py`（`_default_llm_call`）
- Modify: `backend/apps/drama/orchestrator/provider_test.py`（确认仍直连指定 provider，**不**调用 `chat_with_failover`）
- Test: `backend/apps/drama/tests/test_v3_failover_executor.py`
- Modify if needed: 现有 `test_v3_provider_test.py`（断言试连 attempt 数为 0 或不存在 failover 行）

**Interfaces:**
- Consumes: `chat_with_failover`
- Produces: `_default_llm_call` 经 router；需传入 `owner`/`run`/`project`——从 `execute_generation` 已有参数闭包注入（改 `_default_llm_call` 签名或用 contextvars）

推荐：**contextvars** 在 `execute_generation` 入口 set `FailoverCallContext(owner, run, project)`，`_default_llm_call` 读取；避免大面积改 `llm_call` 回调签名。测试用注入 `llm_call=` 仍绕过 router（保持现有单测）；另增测例用 mock `chat_fn` 挂在 router 层。

更稳妥最小改动：
```python
def _default_llm_call(prompt: str, *, role: str = "") -> str:
    from apps.drama.orchestrator.llm_router import chat_with_failover
    ctx = get_failover_call_context()  # 无则 fallback 旧逻辑单跳
    response = chat_with_failover(
        role_key=role or "",
        system_prompt="你是短剧创作助手，只输出合法 JSON。",
        user_prompt=prompt,
        owner=ctx.owner,
        v3_command_run=ctx.run,
        v3_project=ctx.project,
    )
    ...
```

- [ ] **Step 1: Write failing integration test**

`test_v3_failover_executor.py`：seed 项目 + mapping 双 provider；patch `LlmProvider.chat_completion` 侧或 router `chat_fn` 使第一跳失败第二跳返回合法 quality/topic JSON；跑 `execute_generation` 一个轻量命令（如已有 fixture 的 `score_quality` 或 `generate_topic_brief`）；断言 `V3FailoverAttempt` ≥2 且产物写入。

另：`test_connectivity_does_not_create_failover_attempts` — 跑现有试连路径，`V3FailoverAttempt.objects.count()==0`。

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Wire executor + verify provider_test untouched by router**

- [ ] **Step 4: Run failover executor + provider_test — expect OK**

- [ ] **Step 5: Commit** — 跳过

---

### Task 5: Models API 暴露 backup_provider_ids（无 UI）

**Files:**
- Modify: `backend/apps/drama/api/v3/serializers.py`（`RoleModelMappingItemSerializer`）
- Modify: `backend/apps/drama/api/v3/models_service.py`（serialize + put 校验）
- Modify: `docs/contracts/v3/openapi.yaml`（role-mappings schema）
- Modify: `frontend/src/types/v3/domain.ts`（若已有 Mapping 类型）
- Test: 扩展 `test_v3_models_api.py`

**规则：**
- PUT item 可含 `backup_provider_ids: string[]`
- 校验：UUID 存在、≠ 主 provider、去重保序、最多 5 个（写死常量 `MAX_BACKUP_PROVIDERS = 5`）
- GET 回显同字段

- [ ] **Step 1: Failing API test** — PUT 带 backups，GET 见同一列表；主 id 出现在 backup → 400

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run — OK**

- [ ] **Step 5: Commit** — 跳过

---

### Task 6: Logs API + LogsPage 展示 failover_attempts

**Files:**
- Modify: `backend/apps/drama/api/v3/logs_views.py`（run detail）
- Modify: `docs/contracts/v3/openapi.yaml`（`LogRun` / FailoverAttempt schema）
- Modify: `frontend/src/types/v3/domain.ts`
- Modify: `frontend/src/pages/LogsPage.tsx`
- Modify: `frontend/src/pages/LogsPage.test.tsx`
- Test: 扩展 `test_v3_logs_api.py`

**API 形状：**
```json
"failover_attempts": [
  {
    "id": "uuid",
    "attempt_index": 0,
    "provider_id": "uuid",
    "provider_name": "主供应商",
    "status": "failed_switchable",
    "error_code": "http_503",
    "error_message": "…",
    "llm_call_log_id": null,
    "created_at": "ISO-8601"
  }
]
```

UI：详情抽屉「切换尝试」小节；中文状态文案；**不**渲染 operation/recipe。

- [ ] **Step 1: Failing tests** — API 含 attempts；LogsPage 在 mock detail 含 attempts 时可见「切换尝试」/供应商名

- [ ] **Step 2–4: Implement + pass**

- [ ] **Step 5: Commit** — 跳过

---

### Task 7: P2-W1 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`（勾选 W1）

**验收清单（必须机跑）：**

| # | 标准 | 证据 |
|---|------|------|
| 1 | 主挂备通：同 run ≥2 attempt 且生成成功 | `test_v3_llm_router` / `test_v3_failover_executor` |
| 2 | 链耗尽失败且 attempt 全记录 | 同上 |
| 3 | 试连不产生 failover attempt | `test_v3_provider_test` 扩展 |
| 4 | Logs API/UI 展示尝试 | `test_v3_logs_api` + LogsPage test |
| 5 | 无 ECharts/Usage/单价；legacy grep 仍净 | 手检 + `test_v3_legacy_gone` |

机跑：

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models apps.drama.tests.test_v3_failover_policy apps.drama.tests.test_v3_llm_router apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_models_api apps.drama.tests.test_v3_logs_api apps.drama.tests.test_v3_provider_test --settings=config.settings.sqlite_test -v 1
```

```bash
cd frontend && npm test -- --run src/pages/LogsPage.test.tsx && npm run typecheck
```

- [ ] **Step 1: 跑上述命令，全部绿**
- [ ] **Step 2: 写基线 md，勾选结果**
- [ ] **Step 3: 更新 phase2 roadmap W1 状态为 ✅**
- [ ] **Step 4: Commit** — 跳过

---

## Spec Coverage（自检）

| Spec 项 | Task |
|---------|------|
| §4.1 backup_provider_ids | T1, T5 |
| §4.2 V3FailoverAttempt | T1, T3 |
| §3 failover_policy / LlmRouter | T2, T3 |
| §3.2 生成路径接入 | T4 |
| §5 试连不走链 | T4 |
| §6 Logs failover_attempts | T6 |
| §8.2 项 1/2/5 | T7 |
| §4.3–4.4 单价/rollup、§7 /usage、ECharts | **故意延后 W2/W3** |

## 执行交接

Plan 已保存。两种执行方式：

**1. Subagent-Driven（推荐）** — 每 Task 新开子代理，Task 间审查  
**2. Inline Execution** — 本会话按 `executing-plans` 连续做  

选 **1** 或 **2**？

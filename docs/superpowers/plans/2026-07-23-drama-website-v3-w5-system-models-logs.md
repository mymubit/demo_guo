# V3 W5 系统 / 模型 / 日志 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通「系统配置可读写并影响后续运行 → 模型供应商/角色映射/试连可用 → 任意生成可从命令追溯到 LLM 输入输出」三件套，满足设计规格 §8 验收项 4–6。

**Architecture:** 在 `/api/v3` 下新建 system / models / logs 资源面。系统配置用不可变修订表叠 foundation presets；模型配置**复用**既有 `DramaLlmProvider` + `secret_crypto` + `LlmConfigService`（经 v3 适配层暴露，不走 `v2_*`）；试连命令 `test_model_provider` 升为 live。执行日志以 `V3CommandRun` 为轴，把 LLM 调用挂到 `v3_command_run_id`（扩展现有 `DramaLlmCallLog` + `LlmCallContext`，避免双写两套账本）。创作者 UI 替换现有占位 `ModelsPage` / `LogsPage` / `SystemPage`。

**Tech Stack:** 同 W4；试连可 mock HTTP；禁止外网依赖真实供应商；不引入图表库。

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§4–5 系统/模型/日志，§8 项 4–6）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W4 已通过（`docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md`）

## 产品语义（Global）

### 系统配置

- **读：** `GET /api/v3/system/config/` → `{ revision, overlay, effective }`  
  - `effective` = foundation presets（platform-profiles / scoring-presets / production-feasibility / agent-runtime 精简投影）⊕ 最新 overlay  
- **写：** `PUT /api/v3/system/config/` body `{ overlay, change_reason }` → 新建 `V3SystemConfigRevision`（revision+1），返回新 effective  
- Overlay 允许键（W5 最小集，其余忽略并记 warn）：
  - `target_platform`: `generic|douyin|kuaishou|wechat_miniprogram`
  - `scoring_preset`: `standard|strict|relaxed|rhythm_first`
  - `quality_pass_threshold`: number 0–100（可选覆盖预设阈值）
- **生效：** `score_quality` / `check_compliance` / `prepare_delivery` 组 prompt 或门禁读 `resolve_system_config()`；测例断言改 overlay 后下次 resolve 读到新值（可测 resolver，不必真打 LLM）

### 模型配置

| 资源 | 行为 |
|------|------|
| `GET/POST /api/v3/models/providers/` | 列表 / 创建（`api_key` write_only；响应仅 `api_key_set: bool`） |
| `GET/PATCH/DELETE /api/v3/models/providers/{id}/` | 读/改/删；空 key 不覆盖密文 |
| `POST /api/v3/models/providers/{id}/activate/` | 设为唯一 active |
| `GET/PUT /api/v3/models/role-mappings/` | 角色→provider 映射表（缺省用 active provider） |
| `POST …/commands/` `test_model_provider` 或 `POST …/providers/{id}/test/` | 异步或同步试连；写 CONNECTIVITY_TEST 日志 |

角色映射键（中文展示，内部英文 key）：与 recipe `role` 对齐，至少：

`drama-topic-director`, `drama-story-bible`, `drama-episode-designer`, `drama-script-writer`, `drama-script-scorer`, `drama-compliance-guard`, `drama-revision-master`, `drama-delivery-tool`

W5 **不做**：多 Key 轮询、自动故障转移、成本预估图表（UI 可显示 token 字段若日志已有）。

### 执行日志

- `GET /api/v3/logs/runs/?project_id=&status=&command_type=` → `V3CommandRun` 分页列表（owner 隔离）
- `GET /api/v3/logs/runs/{run_id}/` → run + 关联 LLM calls（prompt/response 可截断字段 + 全量详情子资源）
- `GET /api/v3/logs/calls/{call_id}/` → 单次调用快照（脱敏：无 api_key）
- 筛选：项目 / 命令类型 / 状态 / 时间范围（W5 最小）
- UI：列表 + 详情抽屉；**默认不展示** recipe/operation ID；高级折叠区可显示 `command_type`（产品命令英文枚举可接受，禁止 `operation.*`）

### LLM 埋点改造

扩展 `LlmCallContext`：

```python
@dataclass(frozen=True)
class LlmCallContext:
    project_id: str | None = None
    job_id: str | None = None
    v3_command_run_id: str | None = None  # NEW
    v3_project_id: str | None = None      # NEW
    role: str = ""
    purpose: str = "artifact_generation"
    actor: str = "system"
```

`DramaLlmCallLog` 增加可空字段：`v3_command_run` FK → `V3CommandRun`，`v3_project` FK → `V3Project`。  
`skills_bridge/executor.py` 在调用 LLM 前 `llm_call_context(...)` 注入 run/project。  
旧 `DramaProject`/`generation_job` 字段保留，W6 再清理。

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / 配方 ID（日志高级态可显示产品 `command_type`）
- **禁止** `v6_runtime` / `v6_workbench` / `v6_control_plane`；禁止往 `v2_*` 加功能
- 复用 `secret_crypto`、`LlmConfigService`、`LlmProvider`；**不要**经 studio v2 视图
- API Key 永不回传明文；日志/响应脱敏
- 单元测试 mock LLM / 试连 HTTP；禁止外网
- 不引入新第三方库（含图表）
- Commit 仅在用户明确要求时执行（计划 Commit 步骤默认 **跳过**）
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- `DRAMA_SKILLS_ROOT` → 仓库 `drama-skills`

## File Map

| 职责 | 路径 |
|------|------|
| 系统修订 | `models.py` → `V3SystemConfigRevision` |
| 角色映射 | `models.py` → `V3RoleModelMapping` |
| 日志 FK | `DramaLlmCallLog` + migration |
| 配置解析 | `orchestrator/system_config.py`（或 `services/v3_system_config.py`） |
| 模型适配 | `api/v3/models_service.py` 包装 `LlmConfigService` |
| 试连 | `orchestrator` live `test_model_provider` |
| API | `api/v3/system_views.py`、`models_views.py`、`logs_views.py` |
| 契约 | `openapi.yaml`、`commands.md`、TS types |
| 前端 | 重写 `pages/SystemPage.tsx`、`ModelsPage.tsx`、`LogsPage.tsx` + `services/v3/*` |
| 埋点 | `llm_call_context.py`、`llm_call_log_service.py`、`skills_bridge/executor.py` |
| 测试 | `test_v3_system_*`、`test_v3_models_*`、`test_v3_logs_*`；前端 `*.test.tsx` |

## W5 验收标准

1. 可读写系统配置；改 `scoring_preset` / `target_platform` 后 `resolve_system_config()` 返回新值；至少一处生成路径（score 或 compliance fixture 路径）读到该配置（断言注入字段或 resolver 被调用）
2. 可 CRUD 供应商（密钥加密、响应无明文）；可 activate；可配置角色映射
3. `test_model_provider`（或 REST test）成功/失败均可记录日志；测试 mock HTTP
4. 至少一次 V3 异步生成（mock LLM）后，日志 API 能按 `command_run` 查到对应 call 的 prompt/response
5. UI：`/system` `/models` `/logs` 非占位；无 operation ID；无新依赖
6. 回归 W0–W4 仍绿；grep 新路径无 v6_runtime

---

### Task 1: 契约 + OpenAPI 补洞（含 W4 paths）+ TS 类型

**Files:**
- Modify: `docs/contracts/v3/openapi.yaml` — 补 W4 `/projects/{id}/quality/**`、`/delivery/**`；新增 `/system/config/`、`/models/**`、`/logs/**`
- Modify: `commands.md` — `test_model_provider` 说明改为 live
- Modify: `frontend/src/types/v3/domain.ts`（SystemConfig、Provider、RoleMapping、LogRun、LogCall）
- Test: `api.test.ts` 或契约 smoke 扩展

- [ ] **Step 1: 写类型/契约断言失败测**
- [ ] **Step 2: 补 YAML + TS**
- [ ] **Step 3: 测绿**
- [ ] **Step 4: Commit**（跳过）

---

### Task 2: `V3SystemConfigRevision` + resolver

**Files:**
- Modify: `models.py` + migration `0017_…`
- Create: `orchestrator/system_config.py`
- Test: `test_v3_system_config.py`

**Model:**

```python
class V3SystemConfigRevision(models.Model):
    revision = models.PositiveIntegerField(unique=True)
    overlay = models.JSONField(default=dict)
    updated_by = models.CharField(max_length=128)
    change_reason = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_system_config_revision"
        ordering = ["-revision"]
```

**Resolver:**

```python
def resolve_system_config() -> dict:
    """返回 {revision, overlay, effective}；无修订时 revision=0, overlay={}. """
    ...

def save_system_overlay(*, overlay: dict, actor: str, change_reason: str = "") -> dict:
    """校验允许键 → 新 revision → 返回 resolve 结果。"""
    ...
```

`effective` 至少含：`target_platform`, `scoring_preset`, `pass_threshold`, `platform_label_zh`（可从 presets 映射）。

- [ ] **Step 1–3: TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 3: System REST + 配置注入质检路径

**Files:**
- Create: `api/v3/system_views.py`；urls
- Modify: `skills_bridge/executor.py` 或 prompt 组装处 — score/compliance 读取 `resolve_system_config()["effective"]`，把 `scoring_preset` / `target_platform` 写入 user prompt 或 generation params（可测：mock 后断言 prompt 含预设名）
- Test: `test_v3_system_api.py`、扩展 quality async 一测

| Method | Path |
|--------|------|
| GET | `/api/v3/system/config/` |
| PUT | `/api/v3/system/config/` |

权限：登录用户；W5 不做多租户隔离（全局配置，与现有 DramaConfigRevision 一致）。若需按 owner，则 revision 表加 `owner` FK——**本里程碑选全局**，在基线注明。

- [ ] **Step 1–3: API + 注入断言**
- [ ] **Step 4: Commit**（跳过）

---

### Task 4: `V3RoleModelMapping` + Models REST 适配层

**Files:**
- Model + migration（可与 0017 合并若尚未落地，否则 0018）
- Create: `api/v3/models_service.py`、`models_views.py`
- Reuse: `LlmConfigService`、`secret_crypto`
- Test: `test_v3_models_api.py`

**Mapping model:**

```python
class V3RoleModelMapping(models.Model):
    role_key = models.CharField(max_length=64, unique=True)
    provider = models.ForeignKey(DramaLlmProvider, on_delete=models.CASCADE, related_name="role_mappings")
    temperature = models.FloatField(null=True, blank=True)
    max_tokens = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_role_model_mapping"
```

序列化：Provider 响应字段 `id,name,base_url,model_name,temperature,max_tokens,is_enabled,is_active,api_key_set,remark,updated_at` — **无** `api_key`。

- [ ] **Step 1–3: CRUD + activate + 脱敏测**
- [ ] **Step 4: Commit**（跳过）

---

### Task 5: `test_model_provider` live + 映射解析进 executor

**Files:**
- Modify: `orchestrator/types.py` — 从 stub 移除 `test_model_provider`；可放 `ASYNC_LIVE` 或专用 sync test（推荐 **同步**：快速反馈；若用异步须 eager 测）
- Create: `orchestrator/provider_test.py`
- Modify: `executor.py` — 按 recipe.role 查 `V3RoleModelMapping`，有则临时覆盖 ResolvedLlmConfig（或调用 LlmProvider 时传入）；无映射则 active provider
- Test: `test_v3_provider_test.py`（mock `requests`）、映射优先测

试连：对 `base_url` 发最小 chat/completions 或 GET models——对齐现有 studio test 行为，但走 v3。失败人话错误。

**决策（锁定）：** `test_model_provider` 用 **同步** 命令（改 `commands.md` 异步=否），避免排队噪音；payload `{ provider_id }`。

- [ ] **Step 1–3: TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 6: LLM 日志挂 V3 run + Logs REST

**Files:**
- Migration: `DramaLlmCallLog.v3_command_run`、`v3_project` 可空 FK
- Modify: `llm_call_context.py`、`llm_call_log_service.py`、`executor.py`
- Create: `api/v3/logs_views.py`
- Test: `test_v3_logs_api.py`（生成 mock → 断言 call 关联 run）

列表分页：沿用项目既有分页（若无则 `limit/offset` 简单分页，page_size≤50）。

- [ ] **Step 1–3: 埋点 + API TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 7: 前端 SystemPage

**Files:**
- Rewrite: `pages/SystemPage.tsx`、`services/v3/system.ts`、测试
- UI：展示 effective 摘要；表单改 platform / scoring_preset / 可选阈值；保存；中文标签
- 无 operation ID

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 8: 前端 ModelsPage

**Files:**
- Rewrite: `pages/ModelsPage.tsx`、`services/v3/models.ts`、测试
- UI：供应商列表（脱敏）、创建/编辑抽屉、激活、试连按钮与结果；角色映射表（下拉选 provider）
- Key 输入框 write-only；编辑时空=不修改

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 9: 前端 LogsPage

**Files:**
- Rewrite: `pages/LogsPage.tsx`、`services/v3/logs.ts`、测试
- UI：筛选（项目、状态、命令类型）；run 列表；点开看 calls；展开 prompt/response（等宽字体）
- 导出：当前详情 JSON Blob 下载（可选）
- 禁止展示 `operation.*`

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 10: W5 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w5-system-models-logs-acceptance.md`
- Modify: roadmap W5 ✅；下一步 W6

**机跑（示例，按实际模块名调整）：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_system_config apps.drama.tests.test_v3_system_api apps.drama.tests.test_v3_models_api apps.drama.tests.test_v3_provider_test apps.drama.tests.test_v3_logs_api …（含 W0–W4 回归套件） -v 1 --settings=config.settings.sqlite_test

cd frontend
npm test -- src/pages/SystemPage.test.tsx src/pages/ModelsPage.test.tsx src/pages/LogsPage.test.tsx
npm run typecheck
```

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3
```

- [ ] **Step 1: 机跑写入基线**
- [ ] **Step 2: 勾选验收**
- [ ] **Step 3: 通过后方可写 W6**

---

## Self-Review（计划作者）

| Spec §8 | Task |
|---------|------|
| 4 模型配置+试连 | T4–T5、T8 |
| 5 日志追溯 IO | T6、T9 |
| 6 系统配置影响后续运行 | T2–T3、T7 |
| 无 operation ID | T7–T9 |
| 补 W4 OpenAPI paths | T1 |

**刻意不做：** 多 Key 轮询、自动 failover、成本预估图、ECharts 链路图、按 owner 隔离的系统配置、真实外网试连。

# V3 W4 质检 + 交付 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通「已确认正文 → 质量评分 + 合规审查 → 接受问题 → 按问题修订 → 门禁通过后打包交付」闭环，满足设计规格 §8 验收项 2–3。

**Architecture:** 复用 W2/W3 的 `skills_bridge` + Celery + `V3ArtifactVersion`。`score_quality` / `check_compliance` / `prepare_delivery` 为**异步 live、无需用户确认候选**（对齐 `commands.md`「需确认候选=否」）：校验通过后直接写入 **committed** 并 supersede 旧版。`accept_findings` 为同步命令，落 `V3QualityFinding`。`revise_from_findings` 异步产出 `episode_scripts` + `memory_checkpoint` **candidate**，再走既有 `confirm_script_candidate`。交付前用纯 Python `delivery_gate` 判定双报告是否通过；未通过则阻断并返回中文原因。前端新建 `/quality`、`/delivery` 页（不复用 `studio/*`）。

**Tech Stack:** 同 W3；LLM 测试必须 mock；`CELERY_TASK_ALWAYS_EAGER`；**不引入**图表库 / Word / PDF 依赖（十维用 CSS 条形；导出仅 JSON + Markdown）。

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`（§4–5 质检/交付，§8 项 2–3）  
**Roadmap:** `docs/superpowers/plans/2026-07-22-drama-website-v3.md`  
**Prerequisite:** W3 已通过（含 I1/I2 终审修复）

## 产品语义（Global）

### 报告写入模式

| command_type | 模式 | 产物 | 落库 |
|--------------|------|------|------|
| `score_quality` | 异步 live | `quality_report` | 直接 **committed**（supersede 旧） |
| `check_compliance` | 异步 live | `compliance_report` | 直接 **committed** |
| `accept_findings` | **同步**（从 stub 挪出） | 无 LLM | 写 `V3QualityFinding` |
| `revise_from_findings` | 异步 live | `episode_scripts` + `memory_checkpoint` | **candidate**；确认用 `confirm_script_candidate` |
| `prepare_delivery` | 异步 live | `production_package` | 门禁通过后直接 **committed** |

### 报告过期（staleness）

每次生成质量/合规报告时，在 payload 写入：

```json
"_v3_meta": {
  "source_script_version": 3,
  "source_script_artifact_id": "<uuid>"
}
```

（`_v3_meta` 为编排器附加字段；schema 校验前剥离，落库时再合并回 payload，或存于旁路 JSON——**推荐**：校验用剥离后的业务 payload，落库时合并 `_v3_meta`，GET 时计算 `is_stale`。）

`is_stale = true` 当且仅当：当前 committed `episode_scripts.version` ≠ `source_script_version`。  
正文经 `confirm_script_candidate` / `use_drafts` 升版后，旧报告自动过期；UI 提示「正文已更新，请重新评分/合规」。

### 交付门禁（无 LLM）

`delivery_gate.evaluate(project) -> { passed: bool, blockers: list[str] }`：

1. 存在 committed `episode_scripts`，否则阻断「请先确认正文」
2. 存在 **未过期** committed `quality_report`，且 `verdict in ("通过", "条件通过")` **或**（`grade in ("S","A","B")` 且 `needs_revision is False`），否则阻断
3. 存在 **未过期** committed `compliance_report`，且 `overall_result == "通过"`，否则阻断
4. `compliance_report.blocking_issues` 中未在 `V3QualityFinding(status=accepted)` 接受的项 → 阻断（若 `blocking_issues` 为空则跳过）
5. 全部通过 → `passed=True`

`prepare_delivery` 在入队 LLM 前同步跑门禁；失败则 run=`failed`，`error_message` 为人话拼接 `blockers`。

### 阶段推进

- 首次成功的 `score_quality` 或 `check_compliance`：若 `stage == writing` → `stage = quality`
- 成功的 `prepare_delivery`：`stage = delivery`
- 修订确认正文不自动改 stage（可留在 `quality`）

### UI / 导出边界

- **不做** Tiptap、ECharts、Word/PDF 新依赖
- 十维：复用 `frontend/src/utils/reportLabels.ts` + CSS 进度条（可画简易 SVG 雷达，但非必须）
- 交付导出：浏览器下载 `production_package.json` + 由包内字段拼的 `delivery.md`；多格式留 W6+ polish

## Global Constraints

- 创作者 UI 禁止暴露 `operation.*` / 配方 ID
- **禁止** `v6_runtime` / `v6_workbench` / `v6_control_plane`
- 复用 supersede / 幂等 `(owner, command_type, idempotency_key)` 语义
- 单元测试 mock LLM；禁止外网
- 不引入新第三方库
- Commit 仅在用户明确要求时执行（计划中的 Commit 步骤默认 **跳过**）
- 工作目录：`c:\Users\99193\Desktop\demo_guo`
- 后端：`py -3 manage.py test … --settings=config.settings.sqlite_test`
- 本地测前：`DRAMA_SKILLS_ROOT` 指向仓库 `drama-skills`（勿用 `/app/drama-skills`）
- 须有 committed `episode_scripts` 方可评分/合规；门禁通过方可打包

## 命令 / 类型变更

从 `ASYNC_STUB_COMMANDS` 移除：`score_quality`、`check_compliance`、`revise_from_findings`、`prepare_delivery`。  
`accept_findings` 放入新集合 `SYNC_MUTATION_COMMANDS`（或并入 dispatcher 同步分支，与 confirm 并列但非 confirm）。  
`test_model_provider` 仍 stub（W5）。

同步 `docs/contracts/v3/commands.md` 说明：`accept_findings` 为同步；报告类无确认命令。

## File Map

| 职责 | 路径 |
|------|------|
| 问题接受 | `models.py` → `V3QualityFinding` + migration |
| 门禁 | `orchestrator/delivery_gate.py`（新建） |
| 报告元数据 / 过期 | `orchestrator/report_meta.py`（新建） |
| 配方 | `skills_bridge/recipe_map.py` |
| 执行器 | `skills_bridge/executor.py`（direct-commit 路径） |
| 同步命令 | `orchestrator/accept_findings.py` 或扩 `confirm.py` 旁路 |
| 类型 | `orchestrator/types.py`、`dispatcher.py` |
| API | `api/v3/quality_views.py`、`delivery_views.py` |
| 契约 | `commands.md`、`openapi.yaml`、`frontend/src/types/v3/*` |
| 前端 | `pages/QualityPage.tsx`、`pages/DeliveryPage.tsx`、`services/v3/quality.ts`、`delivery.ts` |
| 路由 / CTA | `app/router.tsx`、`pages/projectLabels.ts` |
| Fixture | `tests/fixtures/v3_quality_report.json`、`v3_compliance_report.json`、`v3_production_package.json` |
| 测试 | `test_v3_quality_*`、`test_v3_delivery_*`、`test_v3_delivery_gate.py`；前端对应 `*.test.tsx` |

## W4 验收标准

1. 有 committed 正文时可触发质量评分与合规审查；报告 committed；`stage` 可进 `quality`
2. 报告带 `source_script_version`；正文升版后 GET 返回 `is_stale=true`；过期报告不可用于门禁通过
3. 可 `accept_findings` 接受指定问题；列表可查
4. 可 `revise_from_findings` 得到脚本候选；确认后旧报告过期
5. 双报告未通过 / 过期时 `prepare_delivery` 失败并说明原因；通过后得到 `production_package` committed，`stage=delivery`
6. UI：`/projects/:id/quality`、`/delivery`；概览 CTA 接通；无 operation ID；无新依赖
7. 回归 W0–W3 仍绿；grep 新路径无 v6_runtime

---

### Task 1: 契约说明 + `V3QualityFinding` + report meta 约定

**Files:**
- Modify: `docs/contracts/v3/commands.md`（注明 accept 同步；报告无 confirm）
- Modify: `docs/contracts/v3/openapi.yaml` — QualityState / DeliveryState / Finding
- Modify: `frontend/src/types/v3/domain.ts`、`commands.ts`（若需）
- Modify: `models.py` + migration `0016_v3_quality_finding.py`
- Create: `orchestrator/report_meta.py`
- Test: `test_v3_quality_finding.py`、`test_v3_report_meta.py`

**Interfaces — Finding:**

```python
class V3QualityFinding(models.Model):
    class Source(models.TextChoices):
        QUALITY = "quality", "质量"
        COMPLIANCE = "compliance", "合规"

    class Status(models.TextChoices):
        OPEN = "open", "待处理"
        ACCEPTED = "accepted", "已接受"
        RESOLVED = "resolved", "已解决"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(V3Project, on_delete=models.CASCADE, related_name="quality_findings")
    source = models.CharField(max_length=16, choices=Source.choices)
    finding_key = models.CharField(max_length=128)  # 稳定键：如 defect index 或 hash
    title = models.CharField(max_length=256)
    severity = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    report_artifact = models.ForeignKey(
        V3ArtifactVersion, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_quality_finding"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "source", "finding_key"],
                name="uniq_v3_finding_project_source_key",
            )
        ]
```

**Interfaces — report_meta:**

```python
META_KEY = "_v3_meta"

def attach_script_meta(payload: dict, *, script_art: V3ArtifactVersion) -> dict: ...
def strip_meta_for_validate(payload: dict) -> dict: ...
def read_source_script_version(payload: dict) -> int | None: ...
def is_report_stale(*, report_payload: dict, current_script: V3ArtifactVersion | None) -> bool: ...
```

- [ ] **Step 1: 写失败测试**（唯一约束、`is_report_stale` 真/假）
- [ ] **Step 2: 实现 model + report_meta + 契约字段**
- [ ] **Step 3: 测试通过**
- [ ] **Step 4: Commit**（默认跳过）

---

### Task 2: recipe_map + fixtures + validate

**Files:**
- Modify: `skills_bridge/recipe_map.py`
- Create fixtures:
  - `backend/apps/drama/tests/fixtures/v3_quality_report.json`
  - `v3_compliance_report.json`
  - `v3_production_package.json`
- Test: 扩展 `test_v3_skills_bridge.py` 或新建 `test_v3_quality_recipes.py`

**Recipes:**

```python
"score_quality": {
    "recipe_id": "score-script",
    "role": "drama-score-critic",  # 与 skills 角色名对齐；以 SKILL/operation 为准
    "writes": ["quality_report"],
    "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
    "commit_mode": "direct",  # 执行器识别：成功后写 committed
},
"check_compliance": {
    "recipe_id": "check-compliance",
    "role": "drama-compliance-guard",
    "writes": ["compliance_report"],
    "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
    "commit_mode": "direct",
},
"revise_from_findings": {
    "recipe_id": "revise-script",
    "role": "drama-revision-master",
    "writes": ["episode_scripts", "memory_checkpoint"],
    "requires_committed": ["episode_scripts", "episode_plan", "story_bible"],
    "commit_mode": "candidate",
},
"prepare_delivery": {
    "recipe_id": "prepare-delivery",
    "role": "drama-delivery-tool",
    "writes": ["production_package"],
    "requires_committed": ["episode_scripts", "quality_report", "compliance_report"],
    "commit_mode": "direct",
    "requires_delivery_gate": True,
},
```

Fixture 必须通过 `validate_artifact_payload`（可用最小合法字段；维度 10 个均填 score/weight/evidence/deductions）。

- [ ] **Step 1–3: TDD fixtures + recipe 断言**
- [ ] **Step 4: Commit**（跳过）

---

### Task 3: delivery_gate + executor direct-commit

**Files:**
- Create: `orchestrator/delivery_gate.py`
- Modify: `skills_bridge/executor.py` — 支持 `commit_mode`；生成成功后：
  - `candidate`：现有逻辑
  - `direct`：supersede 同 key 的 committed+candidate，新建 committed，并 `attach_script_meta`
- Test: `test_v3_delivery_gate.py`、`test_v3_quality_executor.py`

**Gate 伪代码：**

```python
def evaluate_delivery_gate(project: V3Project) -> dict:
    blockers: list[str] = []
    scripts = latest(project, "episode_scripts", status=COMMITTED)
    if scripts is None:
        return {"passed": False, "blockers": ["请先确认正文后再交付"]}
    q = latest(project, "quality_report", status=COMMITTED)
    c = latest(project, "compliance_report", status=COMMITTED)
    if q is None or is_report_stale(report_payload=q.payload, current_script=scripts):
        blockers.append("需要有效的质量报告，请重新评分")
    elif not _quality_passes(q.payload):
        blockers.append("质量报告未通过门禁")
    if c is None or is_report_stale(report_payload=c.payload, current_script=scripts):
        blockers.append("需要有效的合规报告，请重新审查")
    elif c.payload.get("overall_result") != "通过":
        blockers.append("合规审查未通过")
    # blocking_issues vs accepted findings ...
    return {"passed": not blockers, "blockers": blockers}
```

- [ ] **Step 1: 门禁用例**（缺报告 / 过期 / 合规不通过 / 全绿）
- [ ] **Step 2: executor direct 路径 + meta**
- [ ] **Step 3: 测绿**
- [ ] **Step 4: Commit**（跳过）

---

### Task 4: 编排 live + accept_findings + stage

**Files:**
- Modify: `orchestrator/types.py`、`dispatcher.py`、`async_runner.py`
- Create: `orchestrator/accept_findings.py`（或 `mutations.py`）
- Modify: `confirm.py` — `confirm_script_candidate` 成功后不必删报告（靠 stale）
- Test: `test_v3_quality_async.py`、`test_v3_accept_findings.py`

**行为：**

1. `score_quality` / `check_compliance`：eager mock → committed 报告；writing→quality
2. `accept_findings` payload：`{ project_id, findings: [{ source, finding_key, title?, severity? }] }` → upsert status=accepted
3. `revise_from_findings` payload：`{ project_id, episode_range?, finding_keys? }` → candidate scripts；确认后 scripts 升版 → 报告 stale
4. `prepare_delivery`：先 gate；失败不调 LLM；成功 → package committed；stage=delivery

- [ ] **Step 1–3: 至少 6 个编排用例**（双报告、过期阻断、accept、revise+confirm、gate 失败、gate 成功）
- [ ] **Step 4: Commit**（跳过）

---

### Task 5: Quality REST API

**Files:**
- Create: `api/v3/quality_views.py`、serializers 扩展
- Modify: `api/v3/urls.py`
- Test: `test_v3_quality_api.py`

**Paths（前缀 `/api/v3/projects/{id}/`）：**

| Method | Path | Command / 行为 |
|--------|------|----------------|
| GET | `quality/` | 返回 quality_report、compliance_report、findings、`is_stale` 标志、latest runs |
| POST | `quality/score/` | → `score_quality` |
| POST | `quality/compliance/` | → `check_compliance` |
| POST | `quality/accept/` | → `accept_findings` |
| POST | `quality/revise/` | → `revise_from_findings` |

响应信封保持 `{ code, message, data }`。人话错误，无 Traceback。

- [ ] **Step 1–3: API TDD**
- [ ] **Step 4: Commit**（跳过）

---

### Task 6: Delivery REST API

**Files:**
- Create: `api/v3/delivery_views.py`
- Modify: `urls.py`
- Test: `test_v3_delivery_api.py`

| Method | Path | 行为 |
|--------|------|------|
| GET | `delivery/` | gate 快照 + package（若有）+ latest_run |
| POST | `delivery/prepare/` | → `prepare_delivery` |

GET 的 `gate` 字段直接调用 `evaluate_delivery_gate`，便于前端禁用按钮并展示 blockers。

- [ ] **Step 1–3: API TDD（含门禁失败 200+failed run）**
- [ ] **Step 4: Commit**（跳过）

---

### Task 7: 前端质检页

**Files:**
- Create: `frontend/src/pages/QualityPage.tsx`、`services/v3/quality.ts`、`QualityPage.test.tsx`
- Modify: `app/router.tsx` — `/projects/:id/quality`
- Optional: `components/quality/DimensionBars.tsx`

**UI：**

- 顶栏：运行「质量评分」「合规审查」；轮询 in-progress run
- 左/中：等级 + 总分 + 十维条（中文维名来自 `reportLabels`）
- 右：问题列表（质量 defects + 合规 blocking/risk）；每项可勾选「接受」后批量提交 accept
- 「按已选问题修订」→ revise；若有脚本 candidate，提示去编辑器确认（或页内确认按钮调 `confirmScriptCandidate`）
- 过期横幅；无正文时禁用并链到编辑器
- **禁止**展示 recipe / operation ID

- [ ] **Step 1–4: 组件测 + typecheck**

---

### Task 8: 前端交付页

**Files:**
- Create: `pages/DeliveryPage.tsx`、`services/v3/delivery.ts`、测试
- Modify: `router.tsx` — `/projects/:id/delivery`

**UI：**

- 展示 gate `passed` / `blockers`（中文）
- `passed` 时可「生成交付包」；否则按钮 disabled
- 有 package 时展示摘要（剧名、复杂度带、清单条数）+「下载 JSON」「下载 Markdown」
- 无 operation ID

- [ ] **Step 1–4: TDD + typecheck**

---

### Task 9: 概览 CTA + 导航打通

**Files:**
- Modify: `pages/projectLabels.ts`、`ProjectOverviewPage.test.tsx`

```typescript
case 'quality':
  return { kind: 'link', to: `/projects/${projectId}/quality`, label: '去质检中心' }
case 'delivery':
  return { kind: 'link', to: `/projects/${projectId}/delivery`, label: '去交付中心' }
```

writing 阶段可保留「去正文编辑」；可选次要链到质检（非必须）。

- [ ] **Step 1–2: 更新测试断言 href**
- [ ] **Step 3: typecheck**

---

### Task 10: W4 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W4 ✅；下一步 W5）

**机跑：**

```bash
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_idempotency apps.drama.tests.test_v3_quality_finding apps.drama.tests.test_v3_report_meta apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_async apps.drama.tests.test_v3_accept_findings apps.drama.tests.test_v3_quality_api apps.drama.tests.test_v3_delivery_api -v 1 --settings=config.settings.sqlite_test

cd frontend
npm test -- src/pages/QualityPage.test.tsx src/pages/DeliveryPage.test.tsx src/pages/ProjectOverviewPage.test.tsx
npm run typecheck
```

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

- [ ] **Step 1: 机跑全绿并写入基线**
- [ ] **Step 2: 勾选验收表**
- [ ] **Step 3: 通过后方可写 W5**

---

## Self-Review（计划作者）

| Spec 要求 | 对应 Task |
|-----------|-----------|
| §8.2 双报告→接受→定向修订→过期语义 | T1 meta、T3–T5、T7 |
| §8.3 门禁打包 / 未通过阻断 | T3 gate、T6、T8 |
| UI 无 operation ID | T7–T9 |
| 无新依赖 / 无 Word PDF | Global + T8 导出边界 |
| 不碰 v6_* | Global Constraints |

**刻意不做（记入基线遗留）：** 像素级剧本定位跳转、真实 Word/PDF、ECharts 雷达、并行单按钮「一键双检」（可用两个按钮；可选后续加）。

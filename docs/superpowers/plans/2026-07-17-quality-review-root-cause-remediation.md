# 评审空壳/模糊结果 · 问题溯源与修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从「评审记录一页只剩分数」这类表象出发，自下而上锁定注入/校验/展示全链路缺陷，完成可回归的加固，使评分官与合规官输出必须带具体证据，且任务所有者能在评审页看到原始 LLM 输入输出。

**Architecture:** 按「症状 → 展示层 → 落库契约 → 生成编排 → Prompt 组装 → 规则/约束 SSOT」六层向上溯源；每层先写失败探测用例，再做最小修复。已落地的部分（section 过滤、评分细则内联、空壳拒绝、任务级调用日志）写入「基线」并补回归锁；剩余缺口（worker 生效确认、合规同等实质校验、schema 示例注入与 SSOT 计划对齐、运维重启清单）按任务推进。

**Tech Stack:** Django + Celery（`apps.drama.services.*`）；`drama-skills` YAML/JSON Schema；React + TanStack Query（`ExternalReviewRecordsPage` / `ArtifactViews` / `JobLlmCallLogsPanel`）；Django `SimpleTestCase` + Vitest。

## Global Constraints

- 禁止引入新第三方库；复用现有 `PromptBuilder` / `SkillsBundleLoader` / `SchemaValidator` / `artifact_normalize`。
- 评分十维与权重 SSOT 仍是 `drama-skills/foundation/constraints/quality-scoring.yaml` + `scoring-presets.yaml`；不得在代码里硬编码第二套权重表作为权威源（内联只允许从 YAML 读取）。
- `quality_report.dimensions.*.evidence` 必须非空且每条 ≥8 字（现行 `score_dimension/1.schema.json`）；禁止再放宽以「先落库再说」。
- 外部评测无 `project` 时，LLM 日志必须对任务所有者可读；不得要求 staff 才能看原始 IO。
- 修改 Celery 路径逻辑后必须在计划验收中写明「重启 worker」；测试通过 ≠ 线上进程已加载新代码。
- 代码注释与测试说明默认中文；commit message 用英文 conventional 前缀（`fix:` / `test:` / `feat:`）。
- 与并行计划 `docs/superpowers/plans/2026-07-17-prompt-schema-field-ssot.md` 的边界：本计划负责裁判产物（`quality_report` / `compliance_report`）实质内容与可观测性；字段表 SSOT 注入由该计划覆盖，本计划只要求裁判角色接上同一管道时补回归断言。

---

## 问题层 → 上游因果树（溯源地图）

```text
【L0 症状】评审记录「一页看完」：十维只有分数；结论/可放行矛盾；
          合规「未命名问题」；看不到原始 prompt/response
                │
                ▼
【L1 展示】ReportArtifactView 无 evidence 则空白；阻断项缺 title；
          调用链误链到 /admin（需 staff）；评审页未内嵌日志
                │
                ▼
【L2 落库契约】schema 曾允许 evidence:[]；normalize 补齐空维；
          verdict 与 needs_revision 未对齐；blocking 无 title
                │
                ▼
【L3 生成编排】json_mode 鼓励最小合法 JSON；空壳可过校验落库；
          纠错只修结构不修「实质空洞」（已部分收紧）
                │
                ▼
【L4 Prompt】quality-scoring.yaml 曾只「点名不内联」；
          输出契约未强制 evidence 形态；知识预算 1200 字被截断
                │
                ▼
【L5 规则注入】collect_rules 按 scope 全量灌 global_core，
          max_chars 硬截断 → 十维权重摘要/九维风险/P2 被挤掉；
          knowledge-sections 未进 loader（已用 role.yaml sections 收窄）
                │
                ▼
【L6 SSOT 文件】规则文件本身不空；问题在「未进入模型上下文」
```

### 已确认根因（本对话实测）

| ID | 层 | 根因 | 证据 |
|----|----|------|------|
| R1 | L5 | `collect_rules` 全量 `global_core` + `max_chars` 截断，裁判关键规则被写作规则挤掉 | 评分官 7501→3600 字丢掉「十维权重摘要」「S级一票否决」；合规丢掉「九维风险评估」「三阶段合规」等 |
| R2 | L4 | `quality-scoring.yaml` 未内联，模型读不到权重/量规 | prompt 仅有路径字符串，无 `weight: 0.15` 等 |
| R3 | L2/L3 | 空 `evidence` 合法 → 空壳评分落库 | 截图十维无证据；fixture 也曾是 `evidence: []` |
| R4 | L2 | `verdict=重大返工` 与 `needs_revision=false/可放行` 并存 | normalize 未对齐 |
| R5 | L1/权限 | 调用链走 admin + 无 project 日志需 staff | `DramaConfigReadPermission`；`LlmCallLogDetailView` 对 `project=null` 拒绝非 staff |
| R6 | L1 | 前端曾 `slice(0,3)` 再削薄（次因） | `ArtifactViews.tsx` |

### 已落地基线（执行本计划前勿回滚）

- `role.yaml` `rule_policy.sections` + `skills_loader.collect_rules` section 过滤与打包优先级
- `prompt_builder._inline_quality_scoring` + quality/compliance 输出契约提示
- `quality_report_evidence_too_sparse` + `score_dimension` `minItems`/`minLength`
- `_reconcile_quality_verdict` / `_normalize_blocking_issues` / 十分制维分放大
- `GET /api/v1/drama/jobs/{id}/llm-logs/` + `JobLlmCallLogsPanel`
- 测试：`test_judge_prompt_injection.py`、`QualityReportNormalizeTests`

---

## File Structure

| 文件 | 职责 |
|------|------|
| `docs/superpowers/plans/2026-07-17-quality-review-root-cause-remediation.md` | **本计划** |
| `backend/apps/drama/services/skills_loader.py` | 规则 section 过滤、打包、知识排序 |
| `backend/apps/drama/services/prompt_builder.py` | 评分细则内联、输出契约 |
| `backend/apps/drama/services/artifact_normalize.py` | 质量/合规归一化、空壳判定、结论对齐 |
| `backend/apps/drama/services/generation_service.py` | 解析→归一化→校验→空壳拒绝→纠错 |
| `backend/apps/drama/views.py` / `urls.py` | 任务级 LLM 日志 API、详情权限 |
| `drama-skills/roles/drama-script-scorer/role.yaml` | sections / max_chars |
| `drama-skills/roles/drama-compliance-guard/role.yaml` | sections / max_chars |
| `drama-skills/schemas/artifacts/score_dimension/1.schema.json` | evidence 非空契约 |
| `frontend/src/pages/ExternalReviewRecordsPage.tsx` | 评审记录 + 调用日志 |
| `frontend/src/components/workbench/JobLlmCallLogsPanel.tsx` | 原始 IO 展示 |
| `frontend/src/components/artifacts/ArtifactViews.tsx` | 评分/合规结构化展示 |
| `backend/apps/drama/tests/test_judge_prompt_injection.py` | 注入回归 |
| `backend/apps/drama/tests/test_artifact_normalize.py` | 归一化/空壳回归 |
| `backend/apps/drama/tests/test_quality_report_substance.py` | **新建**：端到端「空壳必失败 / 有证据才过」 |
| `backend/apps/drama/tests/test_job_llm_logs_access.py` | **新建**：所有者可读无 project 日志 |
| `drama-skills/eval/rubrics/quality_report.yaml` | 可选：评测量规与 evidence 对齐 |

```text
ExternalReviewRecordsPage
  ├─ GenerationJobPanel（进度）
  ├─ JobLlmCallLogsPanel ← GET /jobs/{id}/llm-logs/
  └─ ReportArtifactView(quality|compliance)
         ▲
GenerationService._materialize_artifact_payload
  parse → normalize → schema → sparse check → (repair once)
         ▲
PromptBuilder(role=script-scorer|compliance-guard)
  SKILL + sections规则 + 内联 quality-scoring + schema hints
         ▲
SkillsBundleLoader.collect_rules / load_knowledge_for_role
```

---

### Task 1: 固化 L0→L5 回归探测（防止回退）

**Files:**
- Modify: `backend/apps/drama/tests/test_judge_prompt_injection.py`
- Modify: `backend/apps/drama/tests/test_artifact_normalize.py`（仅补断言，不改生产逻辑除非失败）
- Test: 同上

**Interfaces:**
- Consumes: `SkillsBundleLoader.collect_rules`, `PromptBuilder.build`, `quality_report_evidence_too_sparse`
- Produces: 稳定失败信号——若有人删掉 sections / 内联 / 空壳检查，CI 必红

- [ ] **Step 1: 写失败探测（若基线被回滚应失败的断言）**

在 `test_judge_prompt_injection.py` 追加：

```python
def test_scorer_rules_fit_budget_without_truncating_core(self) -> None:
    text = self.loader.collect_rules(
        "drama.script-scorer", _SETTINGS, max_chars=3600
    )
    self.assertNotIn("...", text[-5:])  # 核心规则应完整装入；若仍截断需先提 max_chars 再测
    self.assertIn("十维权重摘要", text)
    self.assertIn("S级一票否决", text)

def test_compliance_prompt_keeps_nine_dimension_and_phases(self) -> None:
    text = self.loader.collect_rules(
        "drama.compliance-guard", _SETTINGS, max_chars=3200
    )
    self.assertIn("九维风险评估", text)
    self.assertIn("三阶段合规检查", text)
    self.assertIn("P2 建议优化", text)
```

在 `QualityReportNormalizeTests` 追加：

```python
def test_any_dimension_without_evidence_is_sparse(self) -> None:
    from apps.drama.services.artifact_normalize import (
        normalize_quality_report,
        quality_report_evidence_too_sparse,
    )
    dims = {
        k: {"score": 80, "evidence": [f"第1集{k}有明确场景与台词支撑"], "deductions": []}
        for k in (
            "format", "narrative", "conflict", "character", "emotion",
            "logic", "satisfaction", "hooks", "paywall", "genre_fit",
        )
    }
    dims["hooks"] = {"score": 80, "evidence": [], "deductions": []}
    out = normalize_quality_report(
        {"drama_title": "t", "overall_score": 80, "dimensions": dims}, {}
    )
    self.assertTrue(quality_report_evidence_too_sparse(out))
```

- [ ] **Step 2: 跑测确认基线为绿**

```bash
cd backend
set DRAMA_SKILLS_ROOT=../drama-skills
set PYTHONPATH=.
py -3 manage.py test apps.drama.tests.test_judge_prompt_injection apps.drama.tests.test_artifact_normalize.QualityReportNormalizeTests -v2
```

Expected: PASS（若 `test_scorer_rules_fit_budget_without_truncating_core` 因尾部 `...` 失败 → 进入 Task 2 提预算，不要删断言）

- [ ] **Step 3: Commit**

```bash
git add backend/apps/drama/tests/test_judge_prompt_injection.py backend/apps/drama/tests/test_artifact_normalize.py
git commit -m "test: lock judge rule injection and sparse evidence regressions"
```

---

### Task 2: 规则预算与合规实质校验对称加固

**Files:**
- Modify: `drama-skills/roles/drama-script-scorer/role.yaml`
- Modify: `drama-skills/roles/drama-compliance-guard/role.yaml`
- Modify: `backend/apps/drama/services/generation_service.py`（`_parse_normalize_validate`）
- Modify: `backend/apps/drama/services/artifact_normalize.py`（新增 `compliance_report_too_thin`）
- Create: `backend/apps/drama/tests/test_quality_report_substance.py`
- Test: `backend/apps/drama/tests/test_quality_report_substance.py`

**Interfaces:**
- Consumes: `normalize_compliance_report` 结果；`BusinessException(SCHEMA_VALIDATION_FAILED)`
- Produces:
  - `compliance_report_too_thin(payload: dict[str, Any]) -> bool`
  - 判定：`overall_result == "不通过"` 且 `blocking_issues` 非空时，每条必须有非空 `title` 与 `description`（≥8 字）；`risk_items` 每条 `description`/`suggestion` ≥8 字。通过且无风险项则不判定为 thin。

- [ ] **Step 1: 写失败测试**

```python
# backend/apps/drama/tests/test_quality_report_substance.py
from django.test import SimpleTestCase, override_settings

from apps.drama.services.artifact_normalize import (
    compliance_report_too_thin,
    normalize_compliance_report,
)
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class SubstanceGateTests(SimpleTestCase):
    def test_compliance_fail_without_titled_blocking_is_thin(self) -> None:
        raw = {
            "drama_title": "t",
            "overall_result": "不通过",
            "blocking_issues": [{"description": ""}],
            "risk_items": [],
        }
        out = normalize_compliance_report(raw, {})
        self.assertTrue(compliance_report_too_thin(out))

    def test_compliance_pass_with_detailed_p2_ok(self) -> None:
        raw = {
            "drama_title": "t",
            "overall_result": "通过",
            "blocking_issues": [],
            "risk_items": [
                {
                    "type": "p2",
                    "description": "结尾反派缺少明确法律收束，观众易不满",
                    "suggestion": "在终章增加官府处置或判刑场面",
                }
            ],
        }
        out = normalize_compliance_report(raw, {})
        self.assertFalse(compliance_report_too_thin(out))
```

- [ ] **Step 2: 跑测确认失败**

```bash
py -3 manage.py test apps.drama.tests.test_quality_report_substance -v2
```

Expected: FAIL `compliance_report_too_thin` not defined

- [ ] **Step 3: 实现 `compliance_report_too_thin` 并接入 `_parse_normalize_validate`**

```python
def compliance_report_too_thin(payload: dict[str, Any]) -> bool:
    result = str(payload.get("overall_result") or "")
    blocking = payload.get("blocking_issues")
    risks = payload.get("risk_items")
    if not isinstance(blocking, list):
        blocking = []
    if not isinstance(risks, list):
        risks = []
    if result == "不通过" and not blocking:
        return True
    for item in blocking:
        if not isinstance(item, dict):
            return True
        title = str(item.get("title") or "").strip()
        detail = str(item.get("description") or item.get("detail") or "").strip()
        if len(title) < 2 or len(detail) < 8:
            return True
    for item in risks:
        if not isinstance(item, dict):
            return True
        if len(str(item.get("description") or "").strip()) < 8:
            return True
        if len(str(item.get("suggestion") or "").strip()) < 8:
            return True
    return False
```

在 `generation_service._parse_normalize_validate` 于 quality sparse 检查后追加：

```python
if artifact_key == "compliance_report" and compliance_report_too_thin(payload_obj):
    raise BusinessException(
        SCHEMA_VALIDATION_FAILED,
        "合规报告缺少具体阻断/风险描述（title+description）。禁止空标题或空话。",
        http_status=422,
    )
```

若 Task 1 暴露评分规则仍被截断：将 `drama-script-scorer` / `drama-compliance-guard` 的 `max_chars` 分别提到 `4800` / `4000`，并保持 sections 收窄（禁止重新全量 global_core）。

- [ ] **Step 4: 跑测确认通过**

```bash
py -3 manage.py test apps.drama.tests.test_quality_report_substance apps.drama.tests.test_judge_prompt_injection -v2
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add drama-skills/roles/drama-script-scorer/role.yaml drama-skills/roles/drama-compliance-guard/role.yaml backend/apps/drama/services/artifact_normalize.py backend/apps/drama/services/generation_service.py backend/apps/drama/tests/test_quality_report_substance.py
git commit -m "fix: reject thin compliance reports and keep judge rule budget"
```

---

### Task 3: 任务级 LLM 日志权限与评审页可观测性锁死

**Files:**
- Create: `backend/apps/drama/tests/test_job_llm_logs_access.py`（可用 `APIClient`；若本机无 Postgres，改为对 `_assert_job_access` + `list_for_job` 的服务层单测）
- Modify: `frontend/src/components/workbench/JobLlmCallLogsPanel.tsx`（空态文案区分「无权限 / 无数据 / 加载失败」）
- Modify: `frontend/src/pages/ExternalReviewRecordsPage.tsx`（保证日志面板在报告之上且默认展开区域可见）
- Test: `frontend` Vitest 可选；后端以服务层断言为主

**Interfaces:**
- Consumes: `LlmCallLogService.list_for_job(job)`, `GET /api/v1/drama/jobs/<uuid>/llm-logs/?detail=1`
- Produces: 所有者 200 + items；他用户 403

- [ ] **Step 1: 写服务层失败测试**

```python
# 若无法起 DB，用 SimpleTestCase mock QuerySet；有 DB 则 APITestCase
def test_list_for_job_returns_only_that_job_logs(self) -> None:
    # 创建两个 job 的 DramaLlmCallLog，断言 list_for_job(job_a) 不含 job_b
    ...
```

权限用例（有 DB 时）：

```python
def test_owner_can_list_external_job_logs(self) -> None:
    # owner client GET /api/v1/drama/jobs/{id}/llm-logs/ → 200

def test_other_user_cannot_list_external_job_logs(self) -> None:
    # other client → 403
```

- [ ] **Step 2: 跑测**

```bash
py -3 manage.py test apps.drama.tests.test_job_llm_logs_access -v2
```

- [ ] **Step 3: 前端空态**

`JobLlmCallLogsPanel`：

- `isError` → 展示 `formatApiError`（已有）
- `items.length===0` 且任务 `completed` → 「本任务无 LLM 日志记录；请确认 Celery worker 已加载写日志代码并重新评测」
- 卡片默认：第一条 `open=true`（便于一屏看到输入输出）

- [ ] **Step 4: Commit**

```bash
git add backend/apps/drama/tests/test_job_llm_logs_access.py frontend/src/components/workbench/JobLlmCallLogsPanel.tsx frontend/src/pages/ExternalReviewRecordsPage.tsx
git commit -m "fix: ensure review owners can observe job LLM I/O"
```

---

### Task 4: 裁判产物接上 schema 字段表示例（与 SSOT 计划衔接）

**Files:**
- Modify: `backend/apps/drama/services/prompt_builder.py`（若 `schema_prompt_contract` 已存在则调用；否则本任务依赖并行计划 Task 完成后再做）
- Modify: `backend/apps/drama/tests/test_judge_prompt_injection.py`
- Test: 同上

**Interfaces:**
- Consumes: `schema_prompt_contract.extract_required_paths` / `build_output_skeleton`（见 `2026-07-17-prompt-schema-field-ssot.md`）
- Produces: `drama.script-scorer` system prompt 含 `dimensions.format.evidence` 路径或等价嵌套必填说明，以及可过 schema 的最小 `quality_report` 示例片段

- [ ] **Step 1: 写失败断言**

```python
def test_scorer_prompt_includes_quality_report_skeleton_keys(self) -> None:
    builder = PromptBuilder(loader=self.loader)
    system, _ = builder.build(
        "drama.script-scorer",
        settings=_SETTINGS,
        workflow_state={},
        artifacts={},
        latest_script={
            "resolved_script_key": "external_script",
            "value": {"episodes": [{"script": "x"}]},
        },
        scoring_mode="external",
    )
    self.assertIn("evidence", system)
    self.assertIn("deductions", system)
    self.assertIn("dimensions", system)
    self.assertRegex(system, r"format|hooks|genre_fit")
```

- [ ] **Step 2: 最小接入**

仅对 `artifact_key in {"quality_report", "compliance_report"}` 调用已有 `schema_prompt_contract`；若模块尚未合并，本任务标记 blocked 并先完成并行计划 Task 1–3。

- [ ] **Step 3: 跑测 + Commit**

```bash
py -3 manage.py test apps.drama.tests.test_judge_prompt_injection -v2
git commit -m "feat: inject quality/compliance schema skeletons into judge prompts"
```

---

### Task 5: 手工验收清单（进程与真实评测）

**Files:**
- 无代码；产出检查记录可贴到 PR 描述

- [ ] **Step 1: 重启后端与 Celery**

```bash
# Windows 示例：停掉旧 worker 后
cd backend
py -3 -m celery -A config worker -l info
# 同时确保 runserver / 前端 dev 使用当前工作区代码
```

- [ ] **Step 2: 发起外部剧本评测**

路径：`/tools/script-review` → 上传样本 → 打开「评审记录」

验收标准：

1. 「调用日志」可见 ≥2 条（评分 + 合规），可展开 system/user/response  
2. 质量报告每个维度有证据列表；若模型偷懒，任务应为 **失败** 而非空壳成功  
3. 不再出现「总分高 + 重大返工 + 可放行」组合  
4. 合规阻断项有中文标题（非「未命名问题」）

- [ ] **Step 3: 用调用日志反证注入**

在评分官 `system` 中检索：

- `## 评分细则（内联）`
- `叙事效率` / `weight=`
- `十维权重摘要` 或等价评分规则正文  

缺失则回到 Task 1–2，不要只改前端。

---

## 修复与优化建议（计划结论）

### A. 必须做（正确性，本计划 Task 覆盖）

1. **把「空壳」当校验失败，不当软警告**  
   评分：每维 `evidence` 强制非空；合规：不通过必须有带 title/description 的阻断项。否则模型会永远选择最短合法 JSON。

2. **裁判规则注入按 section，不按「整仓 global_core」**  
   继续禁止评分/合规角色吞下台词/AI 腔等写作规则；`max_chars` 只服务已过滤集合。截断策略保持「整块规则丢弃/优先打包」，禁止字符串腰斩关键条。

3. **数值 SSOT 必须内联进 prompt**  
   `quality-scoring.yaml` + 当前 `scoring_preset` 权重继续内联；路径引用对 LLM 无效。

4. **可观测性与权限同级交付**  
   评审记录页内嵌任务级日志；所有者可读；不要把排障能力锁在 admin。

5. **改生成链路必重启 Celery**  
   否则会出现「单测全绿、页面仍一页分数」的假修复。

### B. 应该做（质量，可排期）

6. **与 `prompt-schema-field-ssot` 对齐**  
   给 `quality_report`/`compliance_report` 注入嵌套必填路径 + 最小合法示例，减少靠 normalize 猜字段。

7. **为评分官补 fewshots / anti-examples**  
   `drama-skills/roles/drama-script-scorer/` 目前几乎无 fewshot；加 1–2 条「有集数台词证据」的正例，和「只有分数」的反例。

8. **纠错 prompt 携带失败维度清单**  
   `build_json_repair_user_prompt` 对 sparse 失败附带「hooks/format 缺 evidence」列表，提高一次纠错成功率。

9. **展示层展示 `defects` / `revision_priorities`**  
   即使维内 evidence 短，报告层仍应有可执行返修列表（`ArtifactViews` 已部分支持，需用真实评测验证非空）。

10. **eval 回归**  
    `drama-skills/build/eval_role_llm.py --roles script-scorer,compliance-guard` 增加「evidence 非空率」指标，防止技能仓改动回退。

### C. 不要做（YAGNI / 有害）

11. **不要靠前端「编造」证据** 掩盖空壳。  
12. **不要为通过率再次允许 `evidence: []`。**  
13. **不要把合规重新灌满 `learned_rules` 创作向 LR**（会再次挤掉 P0/P1/九维）。  
14. **不要在未确认 worker 重启前断言「修复无效」。**

### D. 建议验收定义（DoD）

- CI：Task 1–3 相关测试全绿  
- 手工：Task 5 四条全部满足  
- 文档：本计划勾选框随 PR 更新；若与 SSOT 计划并行，在 PR 注明依赖/合并顺序  

---

## Self-Review

1. **Spec coverage:** L0–L6 因果树每层均有「已确认根因」或 Task；剩余缺口落在 Task 2–5 与建议 B。  
2. **Placeholder scan:** 无 TBD；Task 4 对未合并模块写明 blocked 条件而非空实现。  
3. **Type consistency:** `compliance_report_too_thin(payload: dict[str, Any]) -> bool` 与 `quality_report_evidence_too_sparse` 对称；API 路径与现有 `GenerationJobLlmCallLogListView` 一致。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-17-quality-review-root-cause-remediation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — 每个 Task 派新生 subagent，任务间两阶段审查，迭代快  

**2. Inline Execution** — 本会话用 executing-plans 按任务批量执行并设检查点  

Which approach?

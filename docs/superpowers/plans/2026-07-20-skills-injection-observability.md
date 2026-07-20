# 技能注入可观测 Phase 1（A + D 最小注入 Tab）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Spec:** `docs/superpowers/specs/2026-07-20-skills-injection-observability-design.md`  
> **Scope:** 本计划仅 Phase 1（A 全量 + D 最小注入 Tab）。B/C/D 增强见文末 Phase 2+。

**Goal:** 每次角色 LLM 调用落结构化 `InjectionManifest`；Inventory 干跑与真实装配共用同一清单；LLM Logs 详情可看「注入」Tab。

**Architecture:** Loader `assemble_*` 产出 text + 条目元数据 → `PromptBuilder.build` 返回 `(system, user, manifest)` → ContextVar 传给 `LlmCallLogService.record` 写入 `DramaLlmCallLog.injection_manifest` → 详情 API / 前端注入 Tab 展示。

**Tech Stack:** Django ORM + 现有 `PromptBuilder` / `skills_loader` / LLM Logs；React 运维页。禁止新第三方库。

## Global Constraints

- Skills SSOT 仍在 Git `drama-skills/`；不把技能正文搬进 DB
- 禁止引入新第三方库
- Manifest 与 `system_chars` 对账误差 ≤ 64
- 本阶段不改默认注入策略（仍全文；B 另计划）
- 旧日志 `injection_manifest=null` 必须可降级展示
- 层占比用 chars；不做本地 tokenizer

## 文件职责

| 文件 | 职责 |
|------|------|
| Create: `backend/apps/drama/services/injection_manifest.py` | Manifest 构建、对账、类型约定 |
| Modify: `backend/apps/drama/services/skills_loader.py` | `assemble_modules/knowledge/rules_for_role` |
| Modify: `backend/apps/drama/services/prompt_builder.py` | `build` → 三元组 |
| Modify: `backend/apps/drama/services/skills_inventory_service.py` | breakdown 消费 manifest |
| Modify: `backend/apps/drama/services/llm_call_context.py` | ContextVar 挂载 manifest |
| Modify: `backend/apps/drama/services/llm_call_log_service.py` | record / serialize_detail |
| Modify: `backend/apps/drama/models.py` + migration | `injection_manifest` JSONField |
| Modify: `backend/apps/drama/services/generation_service.py` | build 后 set manifest |
| Modify: 所有 `PromptBuilder.build` 调用方 | 解包 3 元组 |
| Create: `backend/apps/drama/tests/test_injection_manifest.py` | 对账 / 结构 / 落库 |
| Modify: `frontend/src/services/admin.ts` | 类型 |
| Modify: `frontend/src/components/ops/llmLogs/CallDetailDrawer.tsx` | 注入 Tab |
| Modify: `frontend/src/components/ops/llmLogs/llmLogUtils.ts` | DetailTab 联合类型 |

---

### Task 1: Manifest 构建模块 + PromptBuilder 三元组

**Files:**
- Create: `backend/apps/drama/services/injection_manifest.py`
- Modify: `backend/apps/drama/services/skills_loader.py`
- Modify: `backend/apps/drama/services/prompt_builder.py`
- Create: `backend/apps/drama/tests/test_injection_manifest.py`
- Modify: 所有 `builder.build` / `prompts.build` 解包处

**Interfaces:**
- Produces:
  - `AssembledLayer` TypedDict / dataclass: `text: str`, `truncated: bool`, 及层相关条目
  - `build_injection_manifest(...) -> dict`
  - `PromptBuilder.build(...) -> tuple[str, str, dict[str, Any]]`
  - `SkillsBundleLoader.assemble_modules_for_role(agent_id, settings) -> dict`（含 `text`, `included`, `skipped`, `truncated`）
  - `assemble_knowledge_for_role` / `assemble_rules_for_role` 同理

- [ ] **Step 1: 写失败测试** `test_injection_manifest.py`

```python
def test_build_returns_manifest_with_layers_and_checksum():
    system, user, manifest = PromptBuilder().build(
        "drama.topic-director",
        settings={...最小合法 settings...},
        workflow_state={},
        artifacts={},
    )
    assert manifest["version"] == 1
    assert manifest["agent_id"] == "drama.topic-director"
    assert "layers" in manifest and "modules" in manifest
    assert abs(manifest["system_chars"] - len(system)) == 0
    assert manifest["checksum"]
    # 对账：各层 chars 之和与 system 差距 ≤ 64（允许标题/换行）
    layer_sum = sum(v["chars"] for v in manifest["layers"].values())
    assert abs(layer_sum - len(system)) <= 64
```

- [ ] **Step 2: 跑测确认失败**

Run: `cd backend && python -m pytest apps/drama/tests/test_injection_manifest.py -v`  
Expected: FAIL（无三元组 / 无模块）

- [ ] **Step 3: 实现 assemble + PromptBuilder**

要点：
- `load_modules_for_role` 保留，内部调 `assemble_modules_for_role` 只返回 `text`
- assemble 时记录 included/skipped（enable_when / missing），与 inventory 现逻辑对齐
- knowledge/rules 记录 truncated 与 max_chars
- `build_injection_manifest` 填 layers（含 header/skill/contract/scoring_inline/fewshots/anti）、policies、checksum=`sha256(system).hexdigest()[:16]`
- 更新 `test_generation.py` / `test_prompt_schema_injection.py` / `test_judge_prompt_injection.py` / `skills_inventory_service` / `generation_service` 解包为 3 值

- [ ] **Step 4: 跑测通过**

Run: `python -m pytest apps/drama/tests/test_injection_manifest.py apps/drama/tests/test_generation.py::PromptBuilderTests apps/drama/tests/test_prompt_schema_injection.py apps/drama/tests/test_judge_prompt_injection.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/apps/drama/services/injection_manifest.py backend/apps/drama/services/skills_loader.py backend/apps/drama/services/prompt_builder.py backend/apps/drama/tests/test_injection_manifest.py backend/apps/drama/tests/test_generation.py backend/apps/drama/tests/test_prompt_schema_injection.py backend/apps/drama/tests/test_judge_prompt_injection.py backend/apps/drama/services/generation_service.py backend/apps/drama/services/skills_inventory_service.py
git commit -m "feat(drama): PromptBuilder returns InjectionManifest"
```

---

### Task 2: Inventory breakdown 统一消费 manifest

**Files:**
- Modify: `backend/apps/drama/services/skills_inventory_service.py`
- Modify: `backend/apps/drama/tests/test_skills_inventory.py`

**Interfaces:**
- Consumes: `PromptBuilder.build` → manifest
- Produces: `build_prompt_breakdown` 的 `layers` / `modules_included` / `modules_skipped` / `system_total` 来自同一 manifest；可增 `knowledge_included` / `knowledge_skipped`（可选，保持旧字段兼容）

- [ ] **Step 1: 改 breakdown 为直接映射 manifest（删手算 included 重复逻辑）**
- [ ] **Step 2: 测试断言 dry-run modules 与 build manifest 一致**
- [ ] **Step 3: Commit** `fix(drama): unify skills inventory breakdown with InjectionManifest`

---

### Task 3: 落库 injection_manifest

**Files:**
- Modify: `backend/apps/drama/models.py`（`DramaLlmCallLog` 加字段）
- Create: `backend/apps/drama/migrations/0007_dramallmcalllog_injection_manifest.py`
- Modify: `backend/apps/drama/services/llm_call_context.py`
- Modify: `backend/apps/drama/services/llm_call_log_service.py`
- Modify: `backend/apps/drama/services/generation_service.py`
- Modify: `backend/apps/drama/tests/test_llm_call_log.py`
- Modify: `backend/apps/drama/tests/test_injection_manifest.py`（增落库用例）

**Interfaces:**
- Produces:
  - `set_injection_manifest(manifest: dict | None)` / `get_injection_manifest() -> dict | None`（独立 ContextVar，不改 frozen `LlmCallContext`）
  - `LlmCallLogService.record(..., injection_manifest: dict | None = None)` 优先显式参数，否则读 ContextVar
  - `serialize_detail` 含 `injection_manifest`
  - `serialize_summary` 可选 `injection_system_chars` / `injection_truncated`（便于列表；若无则省略）

- [ ] **Step 1: 失败测试** — mock LLM 生成路径或直接 `record`+context，断言 DB 字段非空且 detail API 形状正确
- [ ] **Step 2: model + migration + context + record + generation_service 三处 build 后 `set_injection_manifest`**
- [ ] **Step 3: 跑测** `pytest apps/drama/tests/test_llm_call_log.py apps/drama/tests/test_injection_manifest.py -v`
- [ ] **Step 4: Commit** `feat(drama): persist InjectionManifest on DramaLlmCallLog`

---

### Task 4: 前端注入 Tab（D 最小）

**Files:**
- Modify: `frontend/src/services/admin.ts` — `LlmCallLogDetail.injection_manifest`
- Modify: `frontend/src/components/ops/llmLogs/llmLogUtils.ts` — `DetailTab` 含 `'injection'`
- Modify: `frontend/src/components/ops/llmLogs/CallDetailDrawer.tsx` — 注入面板
- Modify: `frontend/src/pages/ops-tools.tokens.test.ts`（若有 Tab 文案契约则补）

**Interfaces:**
- Consumes: detail.injection_manifest（与后端 dict 同形）
- UI：分层 chars 列表 + modules included/skipped + knowledge included/skipped + policies；null 时「无注入清单（历史记录）」

- [ ] **Step 1: 类型 + Tab + 面板（对齐现有 Meta/Prompt 视觉）**
- [ ] **Step 2: 跑** `cd frontend && npx vitest run src/pages/ops-tools.tokens.test.ts`
- [ ] **Step 3: Commit** `feat(frontend): show InjectionManifest tab in LLM call detail`

---

### Task 5: Phase 1 回归闸门

- [ ] **Step 1: 后端** `cd backend && python -m pytest apps/drama/tests/test_injection_manifest.py apps/drama/tests/test_skills_inventory.py apps/drama/tests/test_llm_call_log.py apps/drama/tests/test_generation.py apps/drama/tests/test_prompt_schema_injection.py apps/drama/tests/test_judge_prompt_injection.py -q`
- [ ] **Step 2: 前端** `cd frontend && npx vitest run src/pages/ops-tools.tokens.test.ts`
- [ ] **Step 3: 确认 migration 可应用** `python manage.py migrate drama --plan`

---

## Phase 2+（不在本计划执行；另开 plan）

| Phase | 内容 |
|-------|------|
| 2 / B | 全角色 `evaluate_enable_when`；knowledge/rule 预算；`as_index` 接线；policy flag |
| 3 / C | SSOT validate；Top 文件 exec/ref；SKILL 瘦身；scorer 输出契约 |
| 4 / D+ | 告警、SkillOps 归因、Inventory 真实调用对比 |

---

## Self-Review

1. Spec A §4 + D §7.1 注入 Tab → Task 1–4 覆盖；告警/归因属 Phase 2+。
2. 无 TBD 步骤；调用方解包列入 Task 1。
3. Manifest 字段名与 spec §4.1 一致。

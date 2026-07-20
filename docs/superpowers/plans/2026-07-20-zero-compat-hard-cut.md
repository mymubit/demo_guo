# 零兼容硬切 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除 backend / frontend / drama-skills 中全部向后兼容双读、别名改写、题材 fallback 与重型 JSON 纠错，运行时只认现行契约。

**Architecture:** 契约先行分层硬切：Skills → Runtime（normalize/JSON/题材）→ API/前端 → 测试收紧。不做数据迁移；旧形状直接失败。

**Tech Stack:** Django/DRF、React+TS、drama-skills YAML、pytest、vitest

**Spec:** `docs/superpowers/specs/2026-07-20-zero-compat-hard-cut-design.md`

## Global Constraints

- 零容忍：禁止 `A or B` 字段双读 / 别名静默改写
- 硬切：不做 DB/artifact 迁移
- 交付项唯一名：`deliverables`（含 persist_path `creation_preferences.deliverables`）
- 题材：仅 `genres/matrix.yaml`；删除 `fallback.yaml`；无匹配 → 硬错误
- JSON：围栏剥离 + `json.loads` + 一次尾逗号；禁止 prose 抽取、单引号修复、LLM `json_repair`
- 保留：manifest `bundle_version`、DEPRECATED_TOKENS 防回潮、OpenAI 兼容协议表述
- 禁止新第三方库；提交信息用中文或英文 concise，按仓库风格
- 工作目录：`c:\Users\99193\Desktop\demo_guo`

## File map

| 区域 | 主要文件 |
|------|----------|
| Skills | `workbench.yaml`, `modules/catalog.yaml`, `foundation/rules/genres/*`, `theme-matrix.yaml`, `validate_skills.py`, knowledge docs |
| Runtime | `artifact_normalize.py`, `json_parse.py`, `generation_service.py`, `skills_loader.py`, `condition_eval.py`, `prompt_builder.py` |
| API | `serializers.py`, `views.py`, `job_payload.py` |
| Frontend | `domain.ts`, `App.tsx`, `LlmLogsPage.tsx`, `workbenchDefinition.ts`, `conditions.ts`, `modules.ts`, `settingsForm.ts`, `StageCanvas.tsx`, `NewProjectPage.tsx`, `ArtifactViews.tsx`, fixtures/tests |
| Tests | `test_artifact_normalize.py`, `test_generation.py`, `test_skill_optimization.py`, `test_job_payload.py`, frontend `*.test.ts` |

---

### Task 1: Skills 契约 — deliverables / 删 fallback / 清 dual-lead

**Files:**
- Delete: `drama-skills/foundation/rules/genres/fallback.yaml`
- Modify: `drama-skills/workbench/workbench.yaml`（`delivery_items` → `deliverables`，persist_path 改为 `creation_preferences.deliverables`）
- Modify: `drama-skills/modules/catalog.yaml`（`enable_when` 已用 `deliverables`，确认一致）
- Modify: `drama-skills/build/validate_skills.py`（genres 仅允许 `matrix.yaml`）
- Modify: `drama-skills/foundation/theme-matrix.yaml`（tag prefer 中 `dual-lead` → `returning-elite` 或删除）
- Modify: `drama-skills/knowledge/output-schemas.md`、`knowledge-sections.md`、`knowledge/craft/tier2-genre-rules.md`、`drama-skills/README.md`
- Modify: `drama-skills/EVOLUTION_LOG.md`（追加零兼容硬切记录）
- Modify: `drama-skills/build/lib/condition_eval.py` 与 `backend/.../condition_eval.py` 若存在 deliverables 双读（本任务只改 skills 侧 config_resolver 若需要）
- Test: 跑 `python drama-skills/build/validate_skills.py`

**Interfaces:**
- Produces: workbench 字段 key=`deliverables`，`persist_path=creation_preferences.deliverables`；genres 目录仅 `matrix.yaml`

- [ ] **Step 1:** 删除 `fallback.yaml`；改 `validate_skills.py` 断言 `genre_files == {"matrix.yaml"}`
- [ ] **Step 2:** `workbench.yaml` 全量替换 `delivery_items` 字段名为 `deliverables`，persist/projection 对齐
- [ ] **Step 3:** 清 `dual-lead`；更新 knowledge/README
- [ ] **Step 4:** 运行 `python drama-skills/build/validate_skills.py` → 期望通过
- [ ] **Step 5:** Commit: `chore(skills): hard-cut deliverables and remove genre fallback`

---

### Task 2: Runtime — 题材硬错误 + condition 单键 + JSON 最小集 + 去 LLM repair

**Files:**
- Modify: `backend/apps/drama/services/skills_loader.py`（`_resolve_theme_code`；无有效 theme → raise）
- Modify: `backend/apps/drama/services/condition_eval.py`（只读 `prefs.get("deliverables")`）
- Modify: `drama-skills/build/lib/condition_eval.py`（同步）
- Modify: `backend/apps/drama/services/json_parse.py`（删 `extract_json_object` 路径、单引号、`build_json_repair_user_prompt`；保留围栏+loads+尾逗号）
- Modify: `backend/apps/drama/services/generation_service.py`（删除 json_repair 二次调用整块）
- Modify: `backend/apps/drama/services/prompt_builder.py`（去掉 `schema_required` 注入，只留 `schema_required_paths`）
- Test: `backend/apps/drama/tests/test_generation.py`、`test_skill_optimization.py`；必要时新增 theme resolve 测试

**Interfaces:**
- `parse_llm_json(content) -> dict`：仅围栏+loads+尾逗号
- `module_enable_context`：`"deliverables": prefs.get("deliverables") or []`
- theme 解析失败抛 `BusinessException` 或明确 `ValueError`

- [ ] **Step 1:** 改写/新增失败测试：散文夹 JSON 失败；仅有 `delivery_items` 时 condition 为假；无 matrix/preset 时 loader 报错；删除/改写 `test_build_json_repair_*` 与单引号测试
- [ ] **Step 2:** 跑相关测试确认 RED
- [ ] **Step 3:** 实现最小 JSON / condition / theme / prompt / generation 改动
- [ ] **Step 4:** 跑测试 GREEN
- [ ] **Step 5:** Commit: `refactor(runtime): strip json repair and dual-key condition fallbacks`

---

### Task 3: Runtime — 瘦身 `artifact_normalize`

**Files:**
- Modify: `backend/apps/drama/services/artifact_normalize.py`（删除全部别名与形状改写；保留 settings/matrix 合成补全）
- Modify: `backend/apps/drama/tests/test_artifact_normalize.py`（删 alias 通过用例；改为 alias → schema 失败或 normalize 不改写键名）
- Modify: `backend/apps/drama/tests/test_quality_report_substance.py` 等依赖别名的测试

**Interfaces:**
- `normalize_artifact(key, raw, settings) -> dict`：不重命名 LLM 键；非法形状原样交给 schema（或仅做 settings 字段注入）

- [ ] **Step 1:** 将 `test_llm_loose_aliases_*`、`test_opening_hook_aliases`、`test_compliance_report_aliases` 改为断言「别名键不会被改写成正式键」或删除并由 ingest/schema 失败用例替代
- [ ] **Step 2:** RED
- [ ] **Step 3:** 删除 `_ROLE_TYPE_ALIASES`、hook 别名、对象→string 改写、str(dict) 历史还原、十分制缩放、待补充占位等；更新模块 docstring
- [ ] **Step 4:** GREEN（含 `test_artifact_ingest` / generation 相关）
- [ ] **Step 5:** Commit: `refactor(normalize): remove LLM alias and shape compatibility layer`

---

### Task 4: API + 前端表面清理

**Files:**
- Modify: `backend/apps/drama/serializers.py`、`views.py`、`job_payload.py`
- Modify: `backend/apps/drama/tests/test_job_payload.py`
- Modify: `frontend/src/types/domain.ts`、`workbench.ts`
- Modify: `frontend/src/App.tsx`、`pages/LlmLogsPage.tsx`、`pages/SkillOpsPage.tsx`（chains 链接改 logs）
- Modify: `frontend/src/utils/workbenchDefinition.ts`、`conditions.ts`、`modules.ts`、`settingsForm.ts`、`pipeline.ts`
- Modify: `frontend/src/components/workbench/StageCanvas.tsx`、`pages/NewProjectPage.tsx`
- Modify: `frontend/src/components/artifacts/ArtifactViews.tsx`（删修复稿扁平 legacy）
- Modify: fixtures/tests：`workbenchFixtures.ts`、`workbenchDefinition.test.ts`、`conditions.test.ts`、`settingsForm.test.ts`、`pipeline.test.ts`
- Modify: skills_loader 选项 `id or code` 双读（若仍存在）收紧

- [ ] **Step 1:** 后端/前端测试改为只认新字段；断言旧字段不被读取
- [ ] **Step 2:** RED
- [ ] **Step 3:** 实现表面清理
- [ ] **Step 4:** `pytest` 相关 + `cd frontend && npx vitest run` 相关 → GREEN
- [ ] **Step 5:** Commit: `refactor: remove API and UI backward-compat shims`

---

### Task 5: 全量回归与防回潮扫尾

**Files:** 全仓 grep 确认无残留运行时双读

- [ ] **Step 1:** Grep：`delivery_items`、`fallback.yaml`、`json_repair`、`extract_json_object`、`or request.data.get("filename")`、`bundle_version \|\|`、`open_hook` 映射等
- [ ] **Step 2:** `python drama-skills/build/validate_skills.py`
- [ ] **Step 3:** `cd backend && python -m pytest apps/drama/tests/ -q --tb=line`（或项目惯用命令）
- [ ] **Step 4:** `cd frontend && npx vitest run` 相关失败则修
- [ ] **Step 5:** Commit 若有扫尾：`test: lock zero-compat hard-cut regressions`

---

## Spec coverage checklist

| Spec 节 | Task |
|---------|------|
| §3 deliverables / dual-lead / genres | T1 |
| §4.2 JSON / §4.3 题材 / schema_required / condition | T2 |
| §4.1 normalize | T3 |
| §5 API/前端 | T4 |
| §7 测试 / §9 接受标准 | T2–T5 |

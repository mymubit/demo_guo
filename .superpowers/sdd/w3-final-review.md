# ScriptForge V3 W3 分集+正文 — Final Code Review

**审查范围：** 未提交工作树（只读）  
**计划：** `docs/superpowers/plans/2026-07-23-drama-website-v3-w3-episodes-scripts.md`  
**验收基线：** `docs/superpowers/baselines/2026-07-23-w3-episodes-scripts-acceptance.md`  
**审查日：** 2026-07-23  

---

## 1. Strengths

- **主链闭环完整：** `generate_episode_plan` → `confirm_episode_plan`（`stage=writing`）→ `write_episode_batch` → `confirm_script_candidate` 在 orchestrator + REST + 测试中贯通；`confirm.py` / `executor.py` 的 supersede 语义与 W2 修复一致（生成后淘汰旧 candidate，确认后淘汰旧 committed + 残留 candidate）。
- **局部修订合并正确：** `merge_episode_plan_revision` 仅替换 `episode_numbers` 范围内卡片，范围外 deep copy 保持不变；`test_v3_episode_executor.py` / `test_v3_episodes_async.py` 有专门覆盖。
- **草稿与 AI 候选分离清晰：** `V3ScriptDraft`（`(project, episode_number)` 唯一约束）+ migration `0015`；`PUT …/draft/` 不触碰 `V3ArtifactVersion`；`use_drafts` 路径走 `validate_artifact_payload("episode_scripts", …)`。
- **全局约束遵守：** W3 新代码路径 grep 无 `v6_runtime` / `v6_workbench` / `v6_control_plane`；前端 Episodes/ScriptEditor 无 operation ID / recipe 暴露；未引入 Tiptap。
- **契约同步到位：** `commands.md`、`commands.ts`（含 `confirm_episode_plan`）、`openapi.yaml`、路由 `/episodes` / `/editor`、Overview CTA 矩阵均已对齐。
- **测试与机跑：** 本次复核 W3 相关后端 35 tests OK；前端 Episodes + ScriptEditor + Overview 21 tests OK。

---

## 2. Issues by Severity

### Critical — 0

未发现会导致数据损坏、权限绕过或主链不可用的 Critical 缺陷。supersede、owner 404 隔离、依赖校验（`requires_committed`）在 spot-check 中行为正确。

---

### Important — 2

| # | 问题 | 文件 | 说明 |
|---|------|------|------|
| I1 | **正文草稿自动保存在失败时静默、切换集数可能丢编辑** | `frontend/src/pages/ScriptEditorPage.tsx` | `putScriptDraft` 仅 `.then()` 刷新缓存，无 `.catch()` / 错误态；用户切换集数时 `selectEpisode` 直接 `setDirty(false)`，debounce 定时器被 cleanup 取消，1s 窗口内 edits 未落库即丢失。 |
| I2 | **`use_drafts=true` 只提交 `episode_scripts`，不更新 `memory_checkpoint`** | `backend/apps/drama/orchestrator/confirm.py`（`_commit_script_drafts`） | 人工草稿确认路径 supersede 并新建 committed scripts，但 `memory_checkpoint` 保持旧 committed；后续 `write_episode_batch` 依赖 checkpoint 作上下文时可能不一致。API 已对外暴露 `use_drafts`，测试未断言 checkpoint 行为。 |

---

### Minor — 5

| # | 问题 | 文件 | 说明 |
|---|------|------|------|
| M1 | 前端未暴露「用草稿确认」 | `frontend/src/pages/ScriptEditorPage.tsx` | `confirmScriptCandidate` 硬编码 `use_drafts: false`；验收基线已记为 polish 遗留，不阻塞 W3 主链。 |
| M2 | REST 层未传递 `idempotency_key` | `api/v3/episodes_views.py`、`scripts_views.py` | dispatcher 支持幂等，但 UI 双点会重复建 run（生成路径靠 supersede 自愈；确认无 candidate 时产生 failed run）。与 W0–W2 模式一致。 |
| M3 | 草稿 PUT 无结构校验 | `api/v3/serializers.py`（`ScriptDraftPutSerializer`） | 任意 JSON 可写入；错误延迟到 `use_drafts` confirm 时才以人话失败。W3 可接受。 |
| M4 | `write_episode_batch` 未校验 LLM 返回集数与 `episode_range` 一致 | `skills_bridge/executor.py` | 仅校验 JSON schema；范围错位依赖 LLM/mock，生产需 W4+ 加强。 |
| M5 | 迁移链保留 v6 `DramaScriptDraft`（`0011`）与 V3 `V3ScriptDraft`（`0015`）并存 | `migrations/0011_*.py`、`0015_*.py` | 线性依赖无冲突，但表冗余；W6 清理 v6 时一并处理。 |

---

## 3. Spec Checklist vs W3 Acceptance

| # | 标准 | 审查结论 |
|---|------|----------|
| 1 | 蓝图已确认 → 生成分集候选并确认 → `stage=writing` | **PASS** — `confirm_episode_plan` 仅在 `stage=episodes` 时推进；async/API 测试覆盖。 |
| 2 | `revise_episode_plan` 局部修订，范围外不变 | **PASS** — merge 逻辑 + executor/async/API 测试。 |
| 3 | `write_episode_batch` 1–N 集 → `episode_scripts` (+ checkpoint) 候选 | **PASS** — 双产物同事务创建 + supersede。 |
| 4 | 确认脚本候选；草稿独立不覆盖 committed | **PASS** — 默认 confirm AI candidate；draft PUT 分离；`use_drafts` API 有 validate（见 I2 遗留）。 |
| 5 | UI 分集看板 + 结构化编辑器；无 operation ID | **PASS** — 中文 UI + 测试断言无 recipe id 泄露。 |
| 6 | W0–W2 回归 + mock LLM 新测 | **PASS**（抽样） — W3 子集 35 backend + 21 frontend OK；全量 90+30 与基线一致。 |
| 7 | grep 无 v6_runtime/workbench/control_plane | **PASS** — orchestrator / skills_bridge / tasks_v3 / api/v3 无匹配。 |

**额外全局约束核对：**

| 约束 | 结论 |
|------|------|
| 无新第三方库 / 无 Tiptap | PASS |
| confirm 后 supersede 旧候选 | PASS |
| 幂等 scoped `(owner, command_type, idempotency_key)` | PASS（dispatcher 层；REST 未传 key，见 M2） |
| mock LLM / eager Celery | PASS |

---

## 4. Verdict

| 指标 | 值 |
|------|-----|
| Critical | **0** |
| Important | **2** |
| Minor | 5 |

### Ready for W4? **No**

W3 功能验收与测试基线基本达标，架构延续 W2 模式良好，无 Critical 阻断项。但存在 **2 项 Important**（编辑器草稿持久化可靠性、`use_drafts` 与 checkpoint 一致性），按「Critical+Important 须先修复再进 W4」标准，**建议修复 I1、I2 后再启动 W4**。

**优先修复建议：**

1. **I1：** 切换集数前 flush debounce 或 `await` 保存；autosave 增加 error 提示与重试；失败时保持 `dirty`。
2. **I2：** `use_drafts` 路径同步 supersede/重建 `memory_checkpoint`（或文档明确「草稿确认不更新 checkpoint」并在 API 返回中提示）；补测试。

M1–M5 可在 W4 并行 polish，不阻塞主链开发。

---

*Reviewer: Senior Code Reviewer (read-only, uncommitted tree). 机跑：backend W3 subset 35 OK；frontend 21 OK。*

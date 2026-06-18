# ScriptForge 适配 demo4book 融合技能

> **ARCHIVED（2026-06-18）**：外部 `demo4book` / `ai-drama-skills-v2` 已移除；C 端主链路为独立 Agent + DB 定义。本文档仅作历史资产迁移参考。

## 核心原则（不可颠倒）

| 角色 | 职责 |
|------|------|
| **demo4book / short-drama-script-creator** | 架构 SSOT：`project-config.json`、`schemas/`、`skill-thresholds.json`、`runtime/sub-*` |
| **ScriptForge 网站** | 读技能配置、按 Schema 存 DB、调 CLI、展示进度与报告 |

**禁止**：为迁就网站旧 7 节点引擎而改技能阈值、删节点、改主链终点。

## 网站必须适配的项

1. **主链**：`1→2→3→4→5→6→8`（无 node7 打包；导出为可选 API）
2. **状态机**：`draft → planning → writing → reviewing → scoring → ready | blocked`
3. **完本**：节点6 gate 通过 + 节点8 评分落库 ≥ `releasePassScore`（默认 85）
4. **数据表**：按 `fusion-plan-final.md` §6.6 存 JSONB，不维护 `.shared/`
5. **质检/评分**：`subprocess` 调用 `runtime/sub-gate`、`sub-score`、`sub-compliance`，不在 Python 重写规则

## 已实现（桥接层）

路径：`backend/apps/workflow/fusion/`

| 模块 | 作用 |
|------|------|
| `config_loader.py` | 只读加载 `project-config` / `sub-skills` / `skill-thresholds` |
| `registry.py` | 主链节点 → 网站 `CreationNode` 索引 |
| `cli_runner.py` | 调用 `sub-gate` / `sub-score` / `sub-compliance` |
| `artifact_registry.py` | 节点 index ↔ artifact_key 唯一映射（派生自 schema_registry） |
| `readiness.py` | `ready` 判定（阈值来自技能，不写死 85） |

环境变量（`backend/.env`）：

```env
FUSION_SKILL_ROOT=C:\Users\99193\Desktop\flickplay\demo4book\short-drama-script-creator
FUSION_SKILL_ENABLED=true
```

健康检查：

```bash
cd backend
python manage.py fusion_check
```

## 已接入（2026-06-11）

| 模块 | 说明 |
|------|------|
| `creation/fusion_pipeline.py` | LLM 产出后写临时剧本 → `sub-gate` / `sub-compliance` / `sub-score --bridge` |
| `ProjectFusionArtifact` | JSONB 存 gate、score、brief 等（§6.6） |
| `Project.fusion_status` / `overall_score` / `ready_at` | 融合状态机字段 |
| `tasks._run_creation_pipeline_core` | 流水线结束后自动 `run_fusion_for_project` |
| 进度 API | `get_progress` 返回 `fusion_status`、`score_report_summary` |

迁移：`python manage.py migrate creation`

验证：

```bash
python manage.py fusion_check
python manage.py test_fusion_pipeline --dry-cli
```

## 已完成（2026-06-15 补充接入）

| 模块 | 说明 |
|------|------|
| `workflow/fusion/prompt_builder.py` | `_extract_creation_entry()` + `_ENTRY_PROMPT_HINTS` + `build()`/`build_sub_skill()` 注入。对 `novel-adaptation`（node-11）、`from-reference`（node-12）、`ip-sequel`、`from-outline` 四种入口分支注入专属 system 提示词，覆盖改编约束、原创性要求、IP 硬约束等。 |
| `creation/orchestration/adapt.py` | 已在 submit 时写入 `adaptation_meta` + `project_brief`（含 `novelSourceText`/`referenceFingerprint`/`ipLock`）|
| `skill/config/portal/creation_form_profiles.py` | 所有 5 种入口 profile 已定义（`requiresAdapt`/`validation`/`show` 字段完整）|

## 待完成（网站侧，不动技能）

| 现状 | 目标 |
|------|------|
| 拉片/爆款对标 | 会员 AI 字段实装（`node-9-analysis` 子技能已注册但网站侧未接入）|
| PDF 导出 | Markdown 导出已规划；PDF 二期 |

## 已退役

- `creation/engine/pipeline.py` 不再作为运行路径（仅保留参考）
- `creation/schema_stubs.py` 已删除

## 依赖

- Node.js ≥ 18（与 demo4book `npm install` 同级目录）
- demo4book 已执行 `npm install`（`commander` 依赖）

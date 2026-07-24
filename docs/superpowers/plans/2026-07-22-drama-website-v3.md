# 短剧创作一体机 V3 Implementation Roadmap

> **For agentic workers:** 按里程碑拆分执行。**W0–W6 已全部通过；V3 第一期（phase-1）收口完成。** 后续迭代另开 plan，勿再往已删除的 `v2` / `v6_runtime` 加功能。REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`。

**Goal:** 按 HTML 产品设计大爆炸重写前后端产品面与编排层，第一期交付十大模块 + 套餐 UI 壳。

**Architecture:** React+Vite 前端重写；Django+DRF+Celery 保留框架但产品 API（`/api/v3`）与编排器重建；`drama-skills` 仅作配方包；旧 `/api/v2` 与 studio 在 W6 删除。

**Tech Stack:** React 18、Vite、TypeScript、TanStack Query、Tailwind、Django、DRF、Celery、现有认证信封 `{code,message,data}`

**Spec:** `docs/superpowers/specs/2026-07-22-drama-website-v3-design.md`

## Global Constraints

- 产品真相源：`drama-website-design/drama-website-design.html`
- 不引入新第三方库（前端编辑器若需 Tiptap 须在 W3 plan 中单独说明理由与版本）
- 创作者 UI 禁止暴露 operation ID / artifact key 黑话
- 套餐无支付、无配额扣减
- 禁止往 `v2_*`、`v6_runtime`、`v6_workbench`、`v6_control_plane` 继续加功能
- Commit 仅在用户明确要求时执行
- 工作目录：`c:\Users\99193\Desktop\demo_guo`

## Milestone Index

| 里程碑 | Plan 文件 | 验收摘要 |
|--------|-----------|----------|
| **W0** 契约冻结 | `2026-07-22-drama-website-v3-w0-contracts.md` | ✅ 已通过（见 baselines/2026-07-22-w0-contracts-acceptance.md） |
| **W1** 壳 + 项目 | `2026-07-23-drama-website-v3-w1-shell-projects.md` | ✅ 已通过（见 baselines/2026-07-23-w1-shell-projects-acceptance.md） |
| **W2** 选题 + 蓝图 | `2026-07-23-drama-website-v3-w2-topic-blueprint.md` | ✅ 已通过（见 baselines/2026-07-23-w2-topic-blueprint-acceptance.md） |
| **W3** 分集 + 正文 | `2026-07-23-drama-website-v3-w3-episodes-scripts.md` | ✅ 已通过（见 baselines/2026-07-23-w3-episodes-scripts-acceptance.md） |
| **W4** 质检 + 交付 | `2026-07-23-drama-website-v3-w4-quality-delivery.md` | ✅ 已通过（见 baselines/2026-07-23-w4-quality-delivery-acceptance.md） |
| **W5** 系统/模型/日志 | `2026-07-23-drama-website-v3-w5-system-models-logs.md` | ✅ 已通过（见 baselines/2026-07-23-w5-system-models-logs-acceptance.md） |
| **W6** 套餐壳 + 删旧 | `2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` | ✅ 已通过（见 baselines/2026-07-23-w6-billing-legacy-cut-acceptance.md） |

## Target File Map（全期）

| 区域 | 路径 |
|------|------|
| 契约 | `docs/contracts/v3/`、`frontend/src/types/v3/` |
| 后端 API | `backend/apps/drama/api/v3/` |
| 领域 | `backend/apps/drama/domain/` |
| 编排 | `backend/apps/drama/orchestrator/` |
| Skills 桥 | `backend/apps/drama/skills_bridge/` |
| 前端壳 | `frontend/src/app/`、`frontend/src/pages/`、`frontend/src/projects/` |
| 删除（W6） | `frontend/src/studio/**`、`backend/apps/drama/v2_*`、`services/v6_*.py` |

## Execution Order

1. ✅ 完成并验收 **W0**
2. ✅ 完成并验收 **W1**
3. ✅ 完成并验收 **W2**
4. ✅ 完成并验收 **W3**
5. ✅ 完成并验收 **W4**
6. ✅ 完成并验收 **W5**
7. ✅ 完成并验收 **W6**（Spec §8 全绿；v2/studio 不可达）

**Phase-1 complete：** 第一期十大模块 + 套餐 UI 壳已交付并验收。已知延期见 W6 基线「第一期收口说明」（Tiptap、Word/PDF、真实支付等）。

---

**下一步：** Phase-2 进行中 — Spec `docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`；Roadmap `docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`；当前执行 P2-W1 `…-p2-w1-failover-runtime.md`。

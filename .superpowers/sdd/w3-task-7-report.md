# W3 Task 7 Review — 前端分集看板（只读）

**Date:** 2026-07-23  
**Scope:** `EpisodesPage.tsx`、`services/v3/episodes.ts`、`router.tsx`、`ProjectOverviewPage.tsx`、对应测试  
**Tests:** `EpisodesPage` 6/6、`ProjectOverviewPage`（含 episodes/writing CTA）13/13 OK；`typecheck` PASS

---

## Verdicts

| 维度 | 结论 |
|------|------|
| **Spec** | ✅ |
| **Quality** | Approved |

---

## 必查项

| 项 | 结论 | 依据 |
|----|------|------|
| **中文看板** | ✅ | 标题/按钮/状态/提示均为中文；`RUN_STATUS_LABEL`、`STAGE_LABEL` |
| **生成全剧规划** | ✅ | `generateEpisodePlan`；需 committed 蓝图；run/mutation 忙时禁用 |
| **确认采用** | ✅ | `confirmEpisodePlan`；有 candidate 时显示；测例断言调用 |
| **局部修订（多选）** | ✅ | 仅已确认集可勾选；`reviseEpisodePlan({ episode_numbers })` |
| **无 operation ID** | ✅ | UI 不渲染 `operation.*`/配方/`command_type`；测例 grep 负断言 |
| **轮询 run** | ✅ | `latest_run` 为 `queued|running` 时 `refetchInterval: 2000` |
| **无蓝图禁用+跳转** | ✅ | 禁用生成 +「去故事蓝图」→ `/projects/:id/blueprint` |
| **卡片展示** | ✅ | 标题/钩子/情绪；`<details>` 折叠 JSON 兜底 |
| **路由** | ✅ | `router.tsx`：`/projects/:id/episodes` → `EpisodesPage` |
| **概览 CTA** | ✅ | `stage=episodes` →「去分集规划」；`writing` →「去正文编辑」 |

---

## 测例摘要

| # | 用例 | 结果 |
|---|------|------|
| 1 | 中文 UI、无 op/recipe 泄露 | PASS |
| 2 | 无蓝图：禁用生成 + 链蓝图 | PASS |
| 3 | 点击生成调用 API | PASS |
| 4 | 卡片字段 + 确认采用 | PASS |
| 5 | 多选局部修订 | PASS |
| 6 | run 进行中禁用生成 | PASS |
| 7 | Overview episodes/writing CTA | PASS |

---

## 备注（非阻塞）

1. `writing` CTA 指向 `/editor`，路由由 Task 8 落地；本任务范围仅 CTA 文案与链接。
2. 未单测 `refetchInterval` 轮询（与 Blueprint 页一致）。
3. 局部修订仅对已确认规划；候选只读，符合后端 `revise_episode_plan` 语义。

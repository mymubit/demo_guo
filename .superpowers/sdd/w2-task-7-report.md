# W2 Task 7 审查：前端 Blueprint 页

**Date:** 2026-07-23  
**Scope:** `BlueprintPage.tsx`、`services/v3/blueprint.ts`、路由与概览 CTA（只读审查）  
**Verdict — Spec:** ✅  
**Verdict — Quality:** Approved

---

## Spec 对照

| 要求 | 结果 |
|------|------|
| 5 个中文 Tab：故事蓝图 / 人物 / 世界 / 情绪 / 原创性 | ✅ `BLUEPRINT_TABS` + `Tabs` 组件 |
| 生成 / 确认（含重新生成） | ✅ `generateBlueprint` / `confirmBlueprint`；有 candidate/committed 时按钮为「重新生成」 |
| 无已确认简报时禁用生成 + 依赖提示 | ✅ `canGenerate = hasCommittedBrief && …`；提示 +「去选题定调」链接 |
| 轮询 `latest_run` 至终态 | ✅ `refetchInterval: 2000`（`queued\|running`）；运行中禁用生成 |
| 路由 `/projects/:id/blueprint` | ✅ `router.tsx` → `BlueprintPage` |
| 概览 CTA：`stage=blueprint` →「去故事蓝图」 | ✅ `ProjectOverviewPage` + 测试 |
| 只读预览（无编辑表单） | ✅ `ArtifactPanel` 摘要 + JSON「详细内容」 |
| 无 operation ID / 配方 ID | ✅ UI 与 service 均无 `operation.*` 等 |
| service 三接口对齐 Task 5 API | ✅ GET / POST generate / POST confirm |
| 测试 + typecheck | ✅ Blueprint 6 + Overview 4 PASS；typecheck PASS |

---

## 实现要点

**`blueprint.ts`** — 薄封装 `/api/v3/projects/{id}/blueprint/`，无业务泄漏。

**`BlueprintPage.tsx`** — React Query 拉蓝图状态；额外 `getTopicState` 判断简报依赖；generate/confirm mutation；运行中显示「最近任务：生成中（自动刷新中…）」；不渲染 recipe / run UUID。

---

## 质量备注（非阻塞）

1. 简报依赖经独立 topic 请求判断，非 Blueprint GET 内嵌——多一次往返，W2 可接受。
2. 测试未断言 `refetchInterval` 轮询行为。
3. 产物预览为摘要 + JSON 折叠，非字段级可视化（W2 最小实现）。

---

## 验证

```text
npm test -- src/pages/BlueprintPage.test.tsx src/pages/ProjectOverviewPage.test.tsx  → 10 passed
npm run typecheck                                                                    → PASS
```

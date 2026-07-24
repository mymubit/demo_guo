# W3 Task 9 报告：概览阶段 CTA 与导航打磨

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W3 — 项目概览阶段 CTA 打磨  
**Commits:** none（按要求未 git commit）

---

## What I Implemented

### 1. CTA 矩阵（`resolveOverviewStageCta`）

抽到 `projectLabels.ts`，概览页按阶段渲染：

| stage | CTA | 行为 |
|-------|-----|------|
| `topic` | 去选题定调 | → `/projects/:id/topic` |
| `blueprint` | 去故事蓝图 | → `/projects/:id/blueprint` |
| `episodes` | 去分集规划 | → `/projects/:id/episodes` |
| `writing` | 去正文编辑 | → `/projects/:id/editor` |
| `quality` / `delivery` | 后续开放 | 非链接占位（禁用态样式） |

### 2. `ProjectOverviewPage.tsx`

- 用矩阵替换原先的嵌套三元（修掉 quality/delivery 误落到选题 CTA 的 bug）
- 链接 CTA 保持 action 样式；占位为 muted `span` + `aria-disabled`

### 3. Dashboard

- 未改：`STAGE_LABEL` 已覆盖质检/交付中文文案，无需额外改动

### 4. 测试

- episodes / writing：断言 `href` 分别为 `/episodes`、`/editor`，并导航可达
- quality / delivery：显示「后续开放」，且无任何阶段导航 link

---

## TDD: RED → GREEN

### RED

新增 quality/delivery 用例后：

```text
npm test -- src/pages/ProjectOverviewPage.test.tsx
→ 2 failed | 7 passed（误显「去选题定调」，无「后续开放」）
```

### GREEN

实现矩阵后：

```text
✓ src/pages/ProjectOverviewPage.test.tsx (9 tests)
npm run typecheck → exit 0
```

---

## 验证

```text
npm test -- src/pages/ProjectOverviewPage.test.tsx  → 9 passed
npm run typecheck                                   → PASS
```

未引入新依赖。

---

## Concerns（非阻塞）

1. **质检/交付路由尚未注册**：占位文案正确；W4+ 落地 `/quality`、`/delivery` 后需把 placeholder 换成真实 CTA。
2. Dashboard 卡片仍只展示阶段标签，无「下一步」快捷入口（计划标注可选，本任务未扩）。

---

## Files Touched

- `frontend/src/pages/projectLabels.ts`（`resolveOverviewStageCta`）
- `frontend/src/pages/ProjectOverviewPage.tsx`
- `frontend/src/pages/ProjectOverviewPage.test.tsx`

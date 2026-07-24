# W4 Task 7 报告：前端质检页

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W4 — 前端质检页  
**Commits:** none（用户未要求）

---

## What I Implemented

### 1. `services/v3/quality.ts`（新建）

| Method | Path | 函数 |
|--------|------|------|
| GET | `/api/v3/projects/:id/quality/` | `getQualityState` |
| POST | `…/score/` | `scoreQuality` |
| POST | `…/compliance/` | `checkCompliance` |
| POST | `…/accept/` | `acceptFindings` |
| POST | `…/revise/` | `reviseFromFindings` |

### 2. `pages/QualityPage.tsx` + `components/quality/DimensionBars.tsx`

- 顶栏：质量评分 / 合规审查 / 接受已选 / 按已选修订；轮询 in-progress run
- 左中：等级 + 总分 + 十维 CSS 条（`reportLabels` 中文维名）
- 右：缺陷 + 合规阻断/风险；勾选后批量 accept；修订走 `finding_keys`
- `finding_key` 对齐 `delivery_gate._blocking_issue_key`（blocking: finding_key→id→title）与 defect:`{index}`
- 过期横幅；无 committed 正文禁用并链编辑器；有 script candidate 时页内确认或去编辑器
- 无 recipe / operation ID；无新依赖

### 3. 路由

`/projects/:id/quality` → `QualityPage`

### 4. 测试

`QualityPage.test.tsx`：8 cases（中文 UI、无正文禁用、评分、报告展示、过期、accept、revise、候选确认）

---

## Verification

```powershell
cd frontend
npm test -- src/pages/QualityPage.test.tsx
npm run typecheck
```

**结果：** PASS — **8 tests OK**；**typecheck OK**

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `frontend/src/services/v3/quality.ts` | 新建 |
| `frontend/src/pages/QualityPage.tsx` | 新建 |
| `frontend/src/pages/QualityPage.test.tsx` | 新建 |
| `frontend/src/components/quality/DimensionBars.tsx` | 新建 |
| `frontend/src/app/router.tsx` | 修改 |

---

## Concerns

1. 风险项 `finding_key`（`risk:{index}` / issue 字段）后端 gate 仅比对 blocking；交付门禁不依赖 risk 接受态。
2. 概览 CTA 仍为「后续开放」——属 Task 9 范围。
3. 修订成功后依赖 `scripts.candidate` 展示确认条；若 revise run 成功但 candidate 尚未刷入，需等 query invalidate。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

- 路由 `/projects/:id/quality`、顶栏「质量评分/合规审查/接受已选/按已选修订」、十维 CSS 条（`reportLabels` 中文）、问题列表勾选 accept/revise、过期横幅、无正文禁用+链编辑器、候选确认条均到位。
- 中文 UI；无 operation/recipe ID 泄露；无新依赖。
- `blockingIssueKey` / `qualityDefectKey` 与 `delivery_gate._blocking_issue_key` 一致；测试 8/8 + typecheck 复验通过。
- 已知：`risk:{index}` 不参与交付 gate（报告已记）；`verdict`/`overall_result` 原样展示，若后端英文会混入 UI（低优先级）。

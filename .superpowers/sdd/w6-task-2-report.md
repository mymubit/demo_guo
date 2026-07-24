# W6 Task 2 报告：BillingPage UI

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — BillingPage UI（只读套餐壳）  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-2-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 2

---

## What I Implemented

### 1. `services/v3/billing.ts`（新建）

- `listBillingPlans()` → `GET /api/v3/billing/plans/`，返回 `BillingPlan[]`
- 无购买/配额 API；无新依赖

### 2. `pages/BillingPage.tsx`（重写）

- React Query 拉取三档套餐卡片（name / price_label / features）
- `pro` 卡 `data-featured` + 「最受欢迎」样式
- 购买按钮统一 `disabled`，文案「即将开放」
- 脚注：「当前为展示壳，无支付与配额」
- 中文 UI；无 operation ID

### 3. 测试

- `BillingPage.test.tsx`：三卡文案、featured、脚注+禁用按钮、无 operation ID、加载错误
- `billing.test.ts`：路径与 items 解包

---

## TDD / Verification

```bash
cd frontend
npm test -- src/services/v3/billing.test.ts src/pages/BillingPage.test.tsx
npm run typecheck
```

**结果：** 6 passed（service 1 + page 5）；typecheck exit 0

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `frontend/src/services/v3/billing.ts` | 新建 |
| `frontend/src/services/v3/billing.test.ts` | 新建 |
| `frontend/src/pages/BillingPage.tsx` | 重写 |
| `frontend/src/pages/BillingPage.test.tsx` | 新建 |
| `.superpowers/sdd/w6-task-2-report.md` | 本报告 |

---

## Concerns

1. 按钮仅为展示壳（永远 disabled）；后续接支付需另开任务，勿在本页偷偷加 submit。
2. `featured` 硬编码 `pro`；若后端日后加 `featured` 字段需再对齐。
3. 价位/权益依赖 Task 1 静态 `BILLING_PLANS`；与 HTML §09 旧「免费/¥99」数字差异属计划 intentional override。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

Brief 全满足：三卡（`grid md:grid-cols-3` + API items）、pro featured（`data-featured` + 「最受欢迎」）、脚注「当前为展示壳，无支付与配额」、三按钮 `disabled`「即将开放」、无支付/购买 API、`GET /api/v3/billing/plans/`、无 operation ID、无新依赖。

**Verification:** 6 tests passed；`npm run typecheck` exit 0（复核 2026-07-23）。

**Findings:** No findings.

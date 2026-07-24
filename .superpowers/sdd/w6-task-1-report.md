# W6 Task 1 报告：套餐文案对齐 HTML + 契约/冒烟

**Status:** DONE  
**Date:** 2026-07-23  
**Task:** ScriptForge V3 W6 — 套餐文案对齐 + 契约/冒烟  
**Commits:** none（用户明确跳过）  
**Brief:** `.superpowers/sdd/w6-task-1-brief.md`  
**Plan:** `docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md` Task 1

---

## What I Implemented

### 1. `api/v3/billing_plans.py`（新建，从 views 抽出）

三档只读静态壳：

| id | name | price_label |
|----|------|-------------|
| `basic` | 基础版 | `¥99/月` |
| `pro` | 专业版 | `¥299/月` |
| `team` | 团队版 | `¥999/月` |

features 按计划要点中文压缩（项目/集数/评分合规/导出/分镜宣发/协作/API/客成等），无支付/配额逻辑。

### 2. `api/v3/views.py`

`V3BillingPlansView` 改为 `from …billing_plans import BILLING_PLANS`；删除内联旧「免费/专业/团队」文案。

### 3. 契约与类型

- `docs/contracts/v3/openapi.yaml`：`BillingPlan.id` 枚举 `basic|pro|team`，补 name/price/features 示例
- `frontend/src/types/v3/domain.ts`：`BillingPlan` 注释对齐 id 枚举

### 4. 冒烟 `test_v3_contract_smoke.py`

断言恰好 3 档、id 集合、name/price_label 精确匹配、features 非空列表。

未做：BillingPage UI（Task 2）、git commit。

---

## TDD / Verification

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke --settings=config.settings.sqlite_test -v 2
```

**结果：** Ran 3 tests — OK（含 `test_billing_plans_readonly_shell`）

---

## Concerns

1. 设计稿 HTML §09 仍为「免费 ¥0 / 专业 ¥99 / 团队 ¥299/人/月」；本任务按 **W6 计划表**（basic/pro/team ¥99/¥299/¥999）覆盖旧文案——与原型 HTML 数字不一致，属计划 intentional override。
2. OpenAPI `id` 改为 enum 后，若前端/客户端仍写死 `free` 会契约漂移；Task 2 UI 需跟进。

---

## Reviewer Verdict

**Spec:** ✅  
**Quality:** Approved

- `billing_plans.py` 三档 `basic/pro/team`，`¥99/¥299/¥999` 与 brief/W6 计划表一致；`views` 已抽离引用。
- `test_v3_contract_smoke` 断言 id/name/price/features；本地复跑 3 tests OK。
- OpenAPI `BillingPlan.id` enum + 前端类型注释已对齐；未做 BillingPage（Task 2 范围外）。
- HTML §09 旧价差异已在报告中说明，属计划 intentional override，可接受。

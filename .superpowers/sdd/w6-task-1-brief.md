# W6 Task 1 Brief

Plan: docs/superpowers/plans/2026-07-23-drama-website-v3-w6-billing-legacy-cut.md Task 1

### Task 1: 套餐文案对齐 HTML + 契约/冒烟

Rewrite `BILLING_PLANS` to match design HTML §09:

| id | name | price_label |
|----|------|-------------|
| basic | 基础版 | ¥99/月 |
| pro | 专业版 | ¥299/月 |
| team | 团队版 | ¥999/月 |

Features from plan (can compress slightly but keep meaning).
Update `test_v3_contract_smoke.py` assertions.
Optional: extract `api/v3/billing_plans.py`.

Do NOT build BillingPage UI yet (Task 2).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
sqlite_test.

## Global Constraints
No payment/quota; skip commit; Chinese copy.

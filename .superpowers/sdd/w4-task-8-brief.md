# W4 Task 8 Brief

Plan Task 8: 前端交付页

**Files:**
- Create: `pages/DeliveryPage.tsx`、`services/v3/delivery.ts`、tests
- Modify: `router.tsx` — `/projects/:id/delivery`

**UI:**
- Show gate.passed / gate.blockers (Chinese)
- When passed: enable 「生成交付包」; else disabled
- When package exists: summary (title, complexity band, list counts) + download JSON + download Markdown
- No operation IDs
- No Word/PDF libs — browser Blob downloads only

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
npm test + typecheck.

## Global Constraints
No new deps; Chinese UI.

# W4 Task 7 Brief

Plan Task 7: 前端质检页

**Files:**
- Create: `frontend/src/pages/QualityPage.tsx`、`services/v3/quality.ts`、`QualityPage.test.tsx`
- Modify: `app/router.tsx` — `/projects/:id/quality`
- Optional: `components/quality/DimensionBars.tsx`

**UI:**
- Top: 「质量评分」「合规审查」; poll in-progress runs
- Left/center: grade + overall score + 10 dimension bars (Chinese labels from `frontend/src/utils/reportLabels.ts`)
- Right: findings list (quality defects + compliance blocking/risk); checkbox accept → batch accept API
- 「按已选问题修订」→ revise; if script candidate exists, prompt to editor confirm OR in-page confirmScriptCandidate
- Stale banner; no scripts → disable + link editor
- **NO** recipe/operation IDs in UI
- No new deps (no echarts) — CSS bars OK

Align finding_key with backend gate (read delivery_gate or quality API response keys).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
npm test + typecheck.

## Global Constraints
Chinese UI; no operation IDs; no new third-party libs.

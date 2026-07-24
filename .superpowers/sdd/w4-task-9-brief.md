# W4 Task 9 Brief

Plan Task 9: 概览 CTA + 导航打通

**Files:**
- Modify: `pages/projectLabels.ts`、`ProjectOverviewPage.test.tsx`

```typescript
case 'quality':
  return { kind: 'link', to: `/projects/${projectId}/quality`, label: '去质检中心' }
case 'delivery':
  return { kind: 'link', to: `/projects/${projectId}/delivery`, label: '去交付中心' }
```

Update tests that previously expected placeholder for quality/delivery.
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
npm test ProjectOverviewPage + typecheck.

## Global Constraints
Chinese labels; routes must match Task 7/8.

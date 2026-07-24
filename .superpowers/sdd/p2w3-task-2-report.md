# P2-W3 Task 2 Report — 路由与导航

**Status:** DONE  
**Date:** 2026-07-23  
**Scope:** `/usage` 路由 + 全局导航项（Logs 与 System 之间）

---

## Deliverables

| File | Action |
|------|--------|
| `frontend/src/app/router.tsx` | Modified — import `UsagePage`；`V3_NAV_ITEMS` 新增「用量」；`<Route path="/usage">` |
| `frontend/src/app/router.test.tsx` | Modified — `/usage` 路径、6 项导航、Logs↔System 顺序断言 |

---

## Verification

```powershell
npm test -- --run src/app/router.test.tsx src/pages/UsagePage.test.tsx
npm run typecheck
```

**Result:** 8 tests passed；typecheck OK

---

## Notes

- Nav：`/usage` · label「用量」· hint「Token 与费用」· icon `BarChart3`
- **Commit:** 跳过（按任务要求）

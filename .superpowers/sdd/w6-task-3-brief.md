# W6 Task 3 Brief

Plan Task 3: `/api/v2` 不可达

**Files:**
- Modify: `backend/config/urls.py` — remove `include("apps.drama.v2_urls")`
- Create: V2GoneView — 410 + Chinese message mentioning /api/v3/
- Mount `api/v2/` and `api/v2/<path:rest>`
- Test: `test_v2_gone.py` — `/api/v2/studio/bootstrap/` → 410
- Fix urls comment (no longer "V6 Studio唯一入口")

Do NOT delete v2_* files yet (Task 5).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
sqlite_test.

## Global Constraints
Skip commit; Chinese 410 message.

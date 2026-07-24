# W6 Task 6 Brief

Plan Task 6: 删旧守卫测 + CI 友好断言

Create `backend/apps/drama/tests/test_v3_legacy_gone.py` (or extend existing):
1. Filesystem: assert deleted paths do not exist (v2_*, v6_runtime/workbench/control_plane, generation_service, frontend studio dir)
2. Route: /api/v2/studio/bootstrap/ → 410
3. Source scan: orchestrator / skills_bridge / api/v3 / tasks_v3 — no banned strings v6_runtime|v6_workbench|v6_control_plane|/api/v2/studio
4. Frontend router test still asserts no studio nav (already exists — keep)

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
Run the new tests.

## Global Constraints
Skip commit.

# W6 Task 5 Brief

Plan Task 5: 删除后端 v2_* + Generation/V6 入口

**Order (mandatory):**
1. Confirm Task 3 already removed v2_urls include from config/urls.py
2. Delete: v2_urls.py, v2_views.py, v2_serializers.py, v2_service.py
3. Delete: services/v6_runtime.py, v6_workbench.py, v6_control_plane.py
4. Delete: services/generation_service.py if present
5. Clean tasks.py — remove/rewrite all GenerationService calls; module must still import
6. Delete tests: test_v2_studio_api.py, test_v6_runtime.py, test_generation.py, test_substance_gates_wiring.py (if only old chain)
7. Grep backend/apps/drama (exclude migrations) must find ZERO:
   - from apps.drama.v2
   - apps.drama.services.v6_runtime
   - apps.drama.services.v6_workbench
   - apps.drama.services.v6_control_plane
   - GenerationService
8. No try/except ImportError fake survival

Also check admin.py, other services for imports.
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
Run manage.py check + a smoke subset of v3 tests after cleanup.

## Global Constraints
Skip commit; grep clear = done.

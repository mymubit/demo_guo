# W5 Task 5 Brief

Plan Task 5: test_model_provider live + 映射解析进 executor

**Locked decision:** `test_model_provider` is **SYNC** (commands.md already updated). Payload `{ provider_id }`.

**Files:**
- Modify: `orchestrator/types.py` — remove from ASYNC_STUB; add to SYNC path (SYNC_MUTATION or dedicated)
- Create: `orchestrator/provider_test.py`
- Modify: `dispatcher.py` to run sync test
- Modify: `executor.py` — resolve V3RoleModelMapping by recipe.role; override ResolvedLlmConfig when present
- Optional REST: `POST /api/v3/models/providers/{id}/test/` that calls same logic
- Test: `test_v3_provider_test.py` (mock requests), mapping-priority test

Reuse studio-like connectivity probe pattern but via v3; Chinese error messages; write CONNECTIVITY_TEST log if possible.

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
sqlite_test; mock HTTP — no real network.

## Global Constraints
No v6_*; no new deps; skip commit; never log api_key.

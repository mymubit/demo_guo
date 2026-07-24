# W5 Task 6 Brief

Plan Task 6: LLM 日志挂 V3 run + Logs REST

**Files:**
- Migration: DramaLlmCallLog.v3_command_run FK, v3_project FK (nullable)
- Modify: llm_call_context.py (add v3_command_run_id, v3_project_id), llm_call_log_service.py, skills_bridge/executor.py
- Create: api/v3/logs_views.py + urls
- Test: test_v3_logs_api.py (mock generate → assert call linked to run)

**APIs:**
- GET `/api/v3/logs/runs/?project_id=&status=&command_type=&created_after=&created_before=` — owner-scoped V3CommandRun list, limit/offset ≤50
- GET `/api/v3/logs/runs/{run_id}/` — run + related LLM calls (truncated fields OK)
- GET `/api/v3/logs/calls/{call_id}/` — full snapshot, no api_key

Executor must set llm_call_context with v3 ids before LlmProvider call.
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
sqlite_test + DRAMA_SKILLS_ROOT.

## Global Constraints
No v6_*; no operation IDs required in API; skip commit; desensitize secrets.

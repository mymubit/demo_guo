# W5 Task 3 Brief

Plan Task 3: System REST + 配置注入质检路径

**Files:**
- Create: `api/v3/system_views.py`; modify urls
- Modify: skills_bridge/executor.py or prompt assembly — score/compliance read resolve_system_config()["effective"], inject scoring_preset / target_platform into user prompt or params (testable with mock)
- Test: `test_v3_system_api.py` + extend one quality async/prompt assertion

| Method | Path |
|--------|------|
| GET | `/api/v3/system/config/` |
| PUT | `/api/v3/system/config/` |

Global config (no owner FK) per plan.
Envelope {code,message,data}.
Auth required.
Align overlay validation with Task 2 (ignore unknown keys with warn, or reject invalid enums).

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
DRAMA_SKILLS_ROOT + sqlite_test.

## Global Constraints
No v6_*; mock LLM; skip commit.

# W4 Task 6 Brief

Plan Task 6: Delivery REST API

**Files:**
- Create: `api/v3/delivery_views.py`
- Modify: `urls.py`
- Test: `test_v3_delivery_api.py`

| Method | Path | Behavior |
|--------|------|----------|
| GET | `delivery/` | gate snapshot + package (if any) + latest_run |
| POST | `delivery/prepare/` | → prepare_delivery |

GET `gate` field = `evaluate_delivery_gate` result so UI can disable button + show blockers.
Envelope `{code,message,data}`. Owner isolation.
Follow scripts_views / quality_views patterns.
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
DRAMA_SKILLS_ROOT + sqlite_test.

## Global Constraints
No v6_*; mock LLM; no new deps.

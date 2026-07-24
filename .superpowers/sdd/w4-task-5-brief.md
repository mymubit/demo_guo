# W4 Task 5 Brief

Plan Task 5: Quality REST API

**Files:**
- Create: `api/v3/quality_views.py`、serializers 扩展
- Modify: `api/v3/urls.py`
- Test: `test_v3_quality_api.py`

**Paths under `/api/v3/projects/{id}/`:**

| Method | Path | Behavior |
|--------|------|----------|
| GET | `quality/` | quality_report, compliance_report, findings, is_stale flags, latest runs |
| POST | `quality/score/` | → score_quality |
| POST | `quality/compliance/` | → check_compliance |
| POST | `quality/accept/` | → accept_findings |
| POST | `quality/revise/` | → revise_from_findings |

Envelope `{ code, message, data }`. Human errors, no Traceback.
Owner isolation like other v3 project APIs.
Align finding_key with delivery_gate / accept_findings.
Reuse OpenAPI schemas from Task 1 (QualityState etc.).

Follow patterns in episodes_views.py / scripts_views.py.
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
DRAMA_SKILLS_ROOT + sqlite_test.

## Global Constraints
No v6_*; mock LLM for async posts; no new deps.

# W4 Task 3 Brief

Plan: docs/superpowers/plans/2026-07-23-drama-website-v3-w4-quality-delivery.md

### Task 3: delivery_gate + executor direct-commit

**Files:**
- Create: `orchestrator/delivery_gate.py`
- Modify: `skills_bridge/executor.py` — support `commit_mode`; on success:
  - `candidate`: existing logic
  - `direct`: supersede same-key committed+candidate, create committed, `attach_script_meta`
- Test: `test_v3_delivery_gate.py`、`test_v3_quality_executor.py`

**Gate rules (verbatim from plan):**

`evaluate_delivery_gate(project) -> { passed: bool, blockers: list[str] }`:

1. committed episode_scripts else 「请先确认正文后再交付」
2. non-stale committed quality_report AND (verdict in ("通过","条件通过") OR (grade in S/A/B AND needs_revision is False)) else quality blocker
3. non-stale committed compliance_report AND overall_result == "通过" else compliance blocker
4. blocking_issues not accepted via V3QualityFinding(status=accepted) → block (empty list skip)
5. all pass → passed=True

Use `report_meta.is_report_stale` from Task 1.

**Executor:**
- Read `commit_mode` from recipe (`direct` | `candidate`, default candidate for backward compat)
- For direct reports: strip_meta_for_validate before validate; attach_script_meta from latest committed episode_scripts before save
- Do NOT wire dispatcher/async yet (Task 4) — but executor unit tests can call execute path with mock LLM

Reuse fixtures from Task 2.

Do NOT git commit.

## Global Constraints
- No v6_*
- Mock LLM
- Work: c:\Users\99193\Desktop\demo_guo
- sqlite_test + DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills

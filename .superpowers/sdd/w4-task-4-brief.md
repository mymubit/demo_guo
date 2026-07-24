# W4 Task 4 Brief

Plan Task 4: 编排 live + accept_findings + stage

**Files:**
- Modify: `orchestrator/types.py`、`dispatcher.py`、`async_runner.py`
- Create: `orchestrator/accept_findings.py`（或 mutations.py）
- Modify: confirm.py only if needed (confirm_script_candidate 后靠 stale，不必删报告)
- Test: `test_v3_quality_async.py`、`test_v3_accept_findings.py`

**Behavior (verbatim):**

1. score_quality / check_compliance: eager mock → committed reports; if stage==writing → quality
2. accept_findings payload: `{ project_id, findings: [{ source, finding_key, title?, severity? }] }` → upsert status=accepted
3. revise_from_findings payload: `{ project_id, episode_range?, finding_keys? }` → candidate scripts; after confirm_script_candidate, scripts bump → reports stale
4. prepare_delivery: run evaluate_delivery_gate FIRST; fail → run failed with Chinese blockers, NO LLM; success → package committed; stage=delivery

**types.py changes:**
- Remove from ASYNC_STUB: score_quality, check_compliance, revise_from_findings, prepare_delivery
- Add accept_findings to SYNC_MUTATION_COMMANDS (or sync branch beside confirm)
- Keep test_model_provider stub

**finding_key convention:** align with delivery_gate (read gate code — use same keying for blocking_issues). Document in accept_findings module docstring.

At least 6 orchestration tests: dual reports, stale block, accept, revise+confirm, gate fail, gate success.

Do NOT build REST views (Task 5/6).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills
sqlite_test settings.

## Global Constraints
No v6_*; mock LLM; no new deps; skip commit.

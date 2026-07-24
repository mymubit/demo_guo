# W4 Task 10 Brief

Plan Task 10: W4 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w4-quality-delivery-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md` — mark W4 ✅; next W5

**Cover in baseline:**
- Quality + Delivery API paths
- Commands live in W4
- Frontend routes
- Staleness + gate rules summary
- Test commands you actually run + results
- Known gaps (OpenAPI paths, Word/PDF deferred, etc.)

**Run verification (actually run):**

Backend (set DRAMA_SKILLS_ROOT):
```
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api apps.drama.tests.test_v3_episode_executor apps.drama.tests.test_v3_idempotency apps.drama.tests.test_v3_quality_finding apps.drama.tests.test_v3_report_meta apps.drama.tests.test_v3_delivery_gate apps.drama.tests.test_v3_quality_executor apps.drama.tests.test_v3_quality_async apps.drama.tests.test_v3_accept_findings apps.drama.tests.test_v3_quality_api apps.drama.tests.test_v3_delivery_api -v 1 --settings=config.settings.sqlite_test
```
(If some module names differ slightly, discover with glob and include all W4-related.)

Frontend:
```
npm test -- src/pages/QualityPage.test.tsx src/pages/DeliveryPage.test.tsx src/pages/ProjectOverviewPage.test.tsx src/services/v3/delivery.test.ts
npm run typecheck
```

```
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo

Report: .superpowers/sdd/w4-task-10-report.md
Update .superpowers/sdd/progress-w4.md Task 10 done.

Return: Status, commits none, test summary, baseline path, concerns

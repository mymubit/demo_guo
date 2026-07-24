### Task 10: W3 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w3-episodes-scripts-acceptance.md`
- Modify: roadmap W3 行

- [ ] **Step 1: 回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api apps.drama.tests.test_v3_script_draft apps.drama.tests.test_v3_episodes_async apps.drama.tests.test_v3_episodes_api apps.drama.tests.test_v3_scripts_api -v 1 --settings=config.settings.sqlite_test

cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/pages/EpisodesPage.test.tsx src/pages/ScriptEditorPage.test.tsx
npm run typecheck
```

- [ ] **Step 2: grep**

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

Expected: 无匹配

- [ ] **Step 3: 勾选验收表；通过后方可写 W4**

---


### Task 9: W2 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w2-topic-blueprint-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W2 行指向本 plan）

- [ ] **Step 1: 跑回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud apps.drama.tests.test_v3_artifact apps.drama.tests.test_v3_skills_bridge apps.drama.tests.test_v3_async_commands apps.drama.tests.test_v3_topic_api apps.drama.tests.test_v3_blueprint_api -v 1 --settings=config.settings.sqlite_test

cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx src/pages/TopicPage.test.tsx src/pages/BlueprintPage.test.tsx
npm run typecheck
```

- [ ] **Step 2: grep 验收**

```bash
rg "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/tasks_v3.py backend/apps/drama/api/v3
```

Expected: 无匹配

- [ ] **Step 3: 勾选验收表；全部通过才可写 W3 plan**

---


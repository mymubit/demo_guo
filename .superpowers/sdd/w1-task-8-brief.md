### Task 8: W1 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-w1-shell-projects-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-22-drama-website-v3.md`（W1 行改为指向本 plan）

- [ ] **Step 1: 按「W1 验收标准」逐条勾选并写证据命令/路径**

- [ ] **Step 2: 回归**

```bash
cd backend
py -3 manage.py test apps.drama.tests.test_v3_contract_smoke apps.drama.tests.test_v3_domain_w1 apps.drama.tests.test_v3_orchestrator apps.drama.tests.test_v3_projects_crud -v 1 --settings=config.settings.sqlite_test
cd ../frontend
npm test -- src/types/v3/api.test.ts src/app/router.test.tsx src/services/v3/projects.test.ts src/pages/DashboardPage.test.tsx
npm run typecheck
```

全部绿且验收表勾完 → W1 通过，方可写 W2 plan。

---


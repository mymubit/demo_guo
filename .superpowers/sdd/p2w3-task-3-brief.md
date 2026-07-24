### Task 3: 全量回归 + 基线

机跑：
```powershell
# backend focused P2 + legacy
py -3 manage.py test apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_legacy_gone --settings=config.settings.sqlite_test -v 1
```
```bash
cd frontend && npm test -- --run src/pages/UsagePage.test.tsx src/pages/ModelsPage.test.tsx src/app/router.test.tsx && npm run typecheck
```

验收：`/usage` 可见 token/费用图；无双计；Spec §8.2 项 3；roadmap P2-W3 ✅ phase-2 complete.

- [ ] 写基线 + 更新 roadmap
- [ ] Commit 跳过

---

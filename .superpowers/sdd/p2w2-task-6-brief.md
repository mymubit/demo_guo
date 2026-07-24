### Task 6: P2-W2 验收基线

**Files:** `docs/superpowers/baselines/2026-07-23-p2-w2-prices-usage-api-acceptance.md`；update phase2 roadmap

机跑：
```powershell
py -3 manage.py test apps.drama.tests.test_v3_model_price apps.drama.tests.test_v3_usage_rollup apps.drama.tests.test_v3_prices_api apps.drama.tests.test_v3_usage_api apps.drama.tests.test_v3_models_api --settings=config.settings.sqlite_test -v 1
```
```bash
cd frontend && npm test -- --run src/pages/ModelsPage.test.tsx && npm run typecheck
```

验收项：单价 CRUD；rollup 增量与 unpriced；usage summary owner 隔离；Models 备选 UI；无 ECharts/UsagePage。

- [ ] 全绿 + 写基线 + roadmap ✅
- [ ] Commit 跳过

---

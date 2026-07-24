### Task 7: P2-W1 验收基线

**Files:**
- Create: `docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md`
- Modify: `docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`（勾选 W1）

**验收清单（必须机跑）：**

| # | 标准 | 证据 |
|---|------|------|
| 1 | 主挂备通：同 run ≥2 attempt 且生成成功 | `test_v3_llm_router` / `test_v3_failover_executor` |
| 2 | 链耗尽失败且 attempt 全记录 | 同上 |
| 3 | 试连不产生 failover attempt | `test_v3_provider_test` 扩展 |
| 4 | Logs API/UI 展示尝试 | `test_v3_logs_api` + LogsPage test |
| 5 | 无 ECharts/Usage/单价；legacy grep 仍净 | 手检 + `test_v3_legacy_gone` |

机跑：

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models apps.drama.tests.test_v3_failover_policy apps.drama.tests.test_v3_llm_router apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_models_api apps.drama.tests.test_v3_logs_api apps.drama.tests.test_v3_provider_test --settings=config.settings.sqlite_test -v 1
```

```bash
cd frontend && npm test -- --run src/pages/LogsPage.test.tsx && npm run typecheck
```

- [ ] **Step 1: 跑上述命令，全部绿**
- [ ] **Step 2: 写基线 md，勾选结果**
- [ ] **Step 3: 更新 phase2 roadmap W1 状态为 ✅**
- [ ] **Step 4: Commit** — 跳过

---

# P2-W1 Failover 运行时验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p2-w1-failover-runtime.md` Task 7  
> Roadmap：`docs/superpowers/plans/2026-07-23-drama-website-v3-phase2.md`  
> Spec：`docs/superpowers/specs/2026-07-23-drama-website-v3-phase2-failover-usage-design.md`  
> 验收日：2026-07-23（Task 7 机跑复核）

## P2-W1 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | 主挂备通：同 run ≥2 attempt 且生成成功 | `test_v3_llm_router.test_failover_to_backup_on_switchable_error`；`test_v3_failover_executor.test_execute_generation_failovers_and_writes_attempts`（≥2 attempt，artifact CANDIDATE） | ☑ |
| 2 | 链耗尽失败且 attempt 全记录 | `test_v3_llm_router.test_exhausted_chain_raises_with_zh_summary` | ☑ |
| 3 | 试连不产生 failover attempt | `test_v3_failover_executor.test_connectivity_does_not_create_failover_attempts`；`test_v3_provider_test`（CONNECTIVITY_TEST 仍绿） | ☑ |
| 4 | Logs API/UI 展示尝试 | `test_v3_logs_api.test_run_detail_includes_failover_attempts`；`LogsPage.test.tsx` — `shows failover attempts section…` | ☑ |
| 5 | 无 ECharts/Usage/单价；legacy grep 仍净 | 手检 + `test_v3_legacy_gone`；rg 无匹配 | ☑ |

## 机跑回归（Task 7）

### 后端

```powershell
cd c:\Users\99193\Desktop\demo_guo\backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_failover_models apps.drama.tests.test_v3_failover_policy apps.drama.tests.test_v3_llm_router apps.drama.tests.test_v3_failover_executor apps.drama.tests.test_v3_models_api apps.drama.tests.test_v3_logs_api apps.drama.tests.test_v3_provider_test apps.drama.tests.test_v3_legacy_gone --settings=config.settings.sqlite_test -v 1
```

**结果（2026-07-23）：** `Found 53 test(s)` → **Ran 53 tests in 13.761s — OK**（exit 0）

| 套件 | 覆盖要点 |
|------|----------|
| `test_v3_failover_models` | `V3FailoverAttempt` + mapping `backup_provider_ids` |
| `test_v3_failover_policy` | 链解析 / 可切换错误分类 |
| `test_v3_llm_router` | 主挂备通、链耗尽、终态不切、call 绑定、**env-only hop**（终审 Important 已修） |
| `test_v3_failover_executor` | 生成 failover 写 attempt；试连 0 attempt |
| `test_v3_models_api` | Provider / role-mappings 回归 |
| `test_v3_logs_api` | run detail `failover_attempts` |
| `test_v3_provider_test` | 试连 live + CONNECTIVITY_TEST |
| `test_v3_legacy_gone` | v2/studio Gone；无遗留路径污染 |

### 前端

```bash
cd frontend
npm test -- --run src/pages/LogsPage.test.tsx
npm run typecheck
```

**结果（2026-07-23）：**

- 测试：**8 passed**（1 file）— 含 failover「切换尝试」UI
- typecheck：`tsc -b --pretty false` → exit 0

## 手检 / grep 验收

### 无 ECharts / Usage / 单价（P2-W1 范围）

```powershell
rg -n "echarts|ECharts|/usage|unit_price|单价" frontend/src backend/apps/drama/api/v3
```

**结果：** 无匹配（exit 1 / 0 hits）。`frontend/package.json` 无 `echarts`；无 `/usage` 路由。

### Legacy 仍净

```powershell
rg -n "v6_runtime|v6_workbench|v6_control_plane" backend/apps/drama/orchestrator backend/apps/drama/skills_bridge backend/apps/drama/api/v3 backend/apps/drama/tasks_v3.py
```

**结果：** 无匹配。另：`test_v3_legacy_gone` 机跑 OK。

## 实现物抽查（非阻塞）

| 项 | 证据 | 结果 |
|----|------|------|
| `V3FailoverAttempt` + migration | models + failover tests | ☑ |
| `failover_policy` / `LlmRouter` | `orchestrator` + router/policy tests | ☑ |
| 生成路径写 attempt | `test_v3_failover_executor` | ☑ |
| Logs API `failover_attempts` | `logs_views` + `test_v3_logs_api` | ☑ |
| LogsPage「切换尝试」 | `LogsPage.tsx` + vitest | ☑ |
| 试连不走 failover 链 | executor connectivity 断言 count=0 | ☑ |

## 已知遗留（不阻塞 P2-W1；属后续里程碑）

- **主备链 UI/API 编辑、单价、日 rollup、Usage API**：P2-W2
- **`/usage` + ECharts 图表**：P2-W3（本里程碑刻意不加图表库）
- React Router v7 future flag 警告（测试 stderr），不影响验收
- 本地 shell 若预置 `DRAMA_SKILLS_ROOT=/app/drama-skills`，需覆盖为仓库 `drama-skills` 方可跑测

## 结论

**全部 P2-W1 验收标准已勾选，机跑全绿，无 ECharts/Usage/单价污染，legacy grep 净 → P2-W1 视为通过。** 可撰写并执行 P2-W2。

验收人：Task 7 agent（机跑复核，未 git commit）

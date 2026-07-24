# P2-W2 Task 4 Review — Usage Summary API

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `usage_views.py` + urls + OpenAPI + TS + `services/v3/usage.ts` + `test_v3_usage_api.py`  
**Verdict:** Spec ✅ · Code quality **Changes requested**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `GET /api/v3/usage/summary/` | ✅ `V3UsageSummaryView` + `urls.py` `usage/summary/` |
| Query: `project_id`, `date_from`, `date_to`, `group_by`, `live` | ✅ 全部解析；默认 `group_by=day`，日期默认 today-30d ~ today |
| `timezone` 固定 `Asia/Shanghai` | ✅ 响应写死；`group_by=day` live 桶用 `shanghai_date()` |
| `rows` / `totals` 含 `unpriced_call_count` | ✅ `_empty_metrics` / `_serialize_metrics` / rollup 字段透传 |
| `group_by=day\|model\|command_type` | ✅ 枚举校验 + rollup/live 双路径聚合 |
| 默认读 `V3UsageDailyRollup` | ✅ `owner=request.user` + 日期/project 过滤 |
| `live=1` 合并近 6 小时 `DramaLlmCallLog` | ✅ `_LIVE_HOURS=6` + `_merge_buckets` |
| Owner 隔离 | ✅ rollup `owner=request.user`；live `v3_command_run__owner \| v3_project__owner` |
| OpenAPI path + schemas | ✅ `/usage/summary/`、`UsageMetrics`、`UsageSummary`、`EnvelopeUsageSummary` |
| Frontend types + service | ✅ `domain.ts` + `usage.ts` `getUsageSummary` |
| TDD 11 cases + 独立复跑 | ✅ 见 Verification |

**Notes:** Brief/plan 允许 live 实现取「近窗 call log 重算」或「合并」；当前为叠加合并，符合 brief 字面契约。Phase-2 Spec §4.4 曾写「无单价 `estimated_cost=null`」，Task 4 brief 与 OpenAPI 统一为 `"0.00"` + `unpriced_call_count`，实现与冻结契约一致。

---

## Code quality: Changes requested

视图职责清晰：参数校验 → rollup 聚合 → 可选 live 合并 → 统一序列化。度量累加/格式化抽成纯函数，与 Task 2 `usage_rollup` 复用 `shanghai_date` / `estimate_cost` / `_resolve_command_type`，结构合理。OpenAPI / TS / 后端响应形状对齐。

**阻塞项：** W2 已在 `llm_call_log_service` 同步调用 `apply_call_to_rollup`，`live=1` 仍将近 6 小时 call log **叠加**到 rollup 上，未去重或替换同窗口数据；rollup 成功时近窗 token/费用/次数会**重复计数**。Usage 页（P2-W3）若默认 `live=1` 将展示偏高用量。需在合并前排除已 rollup 的 call、或对近窗以 call log 为准替换 rollup 同日桶，再合入历史 rollup。

---

## Findings

### Critical
*(none)*

### Important

1. **`live=1` 与同步 rollup 重复计数** — Task 2 已在 call log 落库后同步 `apply_call_to_rollup`；`live=1` 对近 6h call log 做 `_merge_buckets` 加法合并，未跳过已入 rollup 的记录。生产路径下 rollup 与 live 同窗重叠时 totals/rows 偏高。单测 `test_live_merges_last_6h_call_logs` 刻意不设 rollup 覆盖 live log（模拟滞后），未覆盖「rollup 已最新」场景。

### Minor

2. **测试缺口 — live owner 隔离** — `test_owner_isolation` 仅覆盖 rollup；无「他户近 6h call log + live=1」断言。
3. **测试缺口 — live unpriced** — rollup 路径有 `test_unpriced_call_count_in_totals`；live 路径无单价 call 未断言 `unpriced_call_count`。
4. **`group_by=model|command_type` 时 live 未按日期窗过滤** — `group_by=day` 对 live key 做 `date_from..date_to` 过滤；model/command_type 分支合入近 6h 全部 live 桶，即使 Shanghai 日落在查询窗外（与 rollup 日期过滤不一致）。
5. **OpenAPI `live` enum 与实现略漂移** — OpenAPI 仅 `"0"|"1"`；实现另接受 `"true"|"True"`（无害，文档未声明）。
6. **测试缺口 — 非法日期 / `date_from > date_to`** — 视图返回 400，无 API 测。
7. **测试缺口 — `live=1` + `group_by=model|command_type`** — 三种 group_by 仅 rollup 覆盖 model/command_type，live 仅 day 路径。

---

## Strengths

- Must 五项（owner 隔离、Asia/Shanghai、unpriced_call_count、group_by、live merge）均有实现与（rollup 或 live）测试锚点。
- Rollup 查询 `owner` 索引过滤；live 使用 `select_related("v3_command_run", "v3_project")` 降低 N+1。
- `estimated_cost` 统一两位小数字符串，与 Prices API 消费端一致。
- `usage.ts` 与 `prices.ts` 同模式（`cleanParams` + `http.get`）；`api.test.ts` 校验 OpenAPI 含 `UsageSummary` 与 `/usage/summary/`。
- 11 条 TDD 覆盖空响应形状、三种 group_by、project 过滤、鉴权、live on/off。

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="c:\Users\99193\Desktop\demo_guo\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_api --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — Ran 11 tests in ~8.1s

```powershell
cd frontend
npm test -- src/types/v3/api.test.ts --run
```

**Result:** OK — 8 tests passed

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 1 |
| Minor | 6 |

# P2-W2 Task 2 Review — V3UsageDailyRollup + increment helper

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Scope:** `V3UsageDailyRollup` model + migration `0022` + `orchestrator/usage_rollup.py` + sync wire in `LlmCallLogService.record` + `test_v3_usage_rollup.py`  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| `shanghai_date(dt) -> date`（Asia/Shanghai 日历日） | ✅ `ZoneInfo("Asia/Shanghai")`；naive datetime 按 UTC 处理；跨日单测 |
| `estimate_cost(...) -> Decimal \| None` | ✅ 查 `V3ModelPrice`；无单价返回 `None`；有单价按 in/out per 1k 计算 |
| `apply_call_to_rollup(call_log)` upsert 累加 | ✅ 维度 date/owner/project/command_type/model/provider；F() 增量更新 |
| 无单价：`estimated_cost` 不加，`unpriced_call_count += 1` | ✅ `cost_delta=0` / `unpriced_delta=1` |
| `command_type` 取自 `v3_command_run.command_type`（可空） | ✅ `_resolve_command_type` + FK 懒查 |
| `provider_id` 由 base_url/model 反查（否则空） | ✅ `_resolve_provider_id`（见 Minor #2 宽松回退） |
| owner：`v3_command_run.owner` → `v3_project.owner`；皆无 skip | ✅ debug log + early return |
| `V3UsageDailyRollup` §4.4 字段 + `unpriced_call_count` | ✅ 全字段 + `uniq_v3_usage_daily_rollup_dims` |
| Migration `0022` depends on `0021` | ✅ |
| Sync wire：`LlmCallLogService.record` create 后调用 | ✅ 唯一生产写路径（`llm_provider.py` 等均经 `record`） |
| TDD：priced / unpriced / same-day upsert / service wire | ✅ 7 tests OK（独立复跑通过） |
| No Usage API / frontend in task artifacts | ✅ |

**Notes:** Brief 要求 sync、无 Celery — 已满足。Spec §4.4 维度与度量与实现对齐；rollup `date` 固定 Asia/Shanghai（与 brief 一致）。

---

## Code quality: Approved

实现聚焦 Task 2 范围：模型 + 增量 helper + 单写路径同步接线。`apply_call_to_rollup` 使用 `transaction.atomic` + `select_for_update` + `IntegrityError` 重试，并发 upsert 合理。TDD RED→GREEN 证据可信；`config.settings.sqlite_test` 下 7 用例全部通过。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor

1. **SQLite W047** — `nulls_distinct=False` 唯一约束在 SQLite 测试库不生效；报告已说明，应用层 upsert 仍正确；PostgreSQL 生产约束生效。
2. **`_resolve_provider_id` 宽松回退** — base_url 命中但 `model_name` 未匹配时仍返回该 base_url 下首个 provider；brief 字面为「反查不到则空」。同 base_url 多 provider 时可能错配 provider/单价（当前数据模型下风险低）。
3. **Rollup 失败不阻断 log 写入** — `LlmCallLogService.record` 捕获 `apply_call_to_rollup` 异常并 `logger.exception`；call log 成功但 rollup 可能缺失，需靠日志监控（W2 可接受，后续可考虑 metrics/重放）。
4. **测试覆盖缺口** — 无 owner-less skip、provider 仅 base_url 回退、rollup 异常路径用例（brief 必测项已覆盖）。
5. **无 rollup 维度查询索引** — 当前仅唯一约束；Usage API（Task 4+）高频按 date/owner 聚合时可能需补充索引（非本 task 范围）。

---

## Strengths

- Must-have API 面完整：`shanghai_date` / `estimate_cost` / `apply_call_to_rollup` 签名与 docstring 与 brief 一致。
- `unpriced_call_count` 一期必带，避免未定价 call 静默丢失。
- 同日 upsert、priced/unpriced 分支、success/error 分别累加 `call_count`/`success_count` 行为清晰。
- 接线点正确：`DramaLlmCallLog.objects.create` 仅存在于 `LlmCallLogService.record`，wire 覆盖全部生产写路径。
- 测试含 UTC→上海跨日、`RecordWiresRollupTests` 端到端验证。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 5 |

---

## Verification

```powershell
cd backend
$env:DRAMA_SKILLS_ROOT="...\drama-skills"
py -3 manage.py test apps.drama.tests.test_v3_usage_rollup --settings=config.settings.sqlite_test -v 1
```

**Result:** OK — Ran 7 tests in ~1.5s

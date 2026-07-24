# P2-W1 Task 3 Review — llm_router 按链调用并写 FailoverAttempt

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Artifacts:** working tree (`llm_router.py`, `test_v3_llm_router.py`；`p2w1-task-3-review-pkg.md` 缺失，直接审读实现)  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| 仅 `orchestrator/llm_router.py` + `test_v3_llm_router.py`；无 executor / provider_test 接线 | ✅ |
| `chat_with_failover` 签名与 brief 一致（含可注入 `chat_fn`） | ✅ |
| 消费 `resolve_chain` + `classify_provider_error`；每 hop 写 `V3FailoverAttempt` | ✅ |
| 调用 `chat_fn(..., config=hop.config)`；默认 `LlmProvider.chat_completion` | ✅ |
| 成功 → `succeeded` + 弱绑定同 run 最新 `DramaLlmCallLog` | ✅ |
| 可切换失败 → `failed_switchable` 并继续下一跳 | ✅ |
| 不可切换失败 → `failed_terminal` 并原样 re-raise | ✅ |
| 链耗尽 → `LlmProviderError`，message 含「已尝试供应商」与名称列表 | ✅ |
| 单测 mock `chat_fn`，无真实网络 | ✅ |
| brief 三例 + call-log 绑定；独立复跑 OK（4 tests） | ✅ |

**Scope note:** 空 / 缺失 `provider_id` 或 DB 中已删 provider 的 hop 被静默跳过、不写 `SKIPPED` attempt；整链皆跳过时耗尽文案为「已尝试供应商：(无)」。brief 未要求 SKIPPED 审计，report 已自述，Task 4 executor 接入前可接受。

---

## Code quality: Approved

职责单一、流程与 brief 逐步对应；`_sanitize_error_message` / `_exhausted_error` 抽取合理；终态失败保留原始异常、可切换耗尽用 `raise err from last_exc` 便于排查。TDD RED→GREEN 有 report 证据且复验通过。无 scope creep。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor
1. **空链 / 全跳过路径无单测** — `(无)` 耗尽文案与 report 自述一致，但未覆盖。
2. **brief 建议的 `ValueError` 终态路径未测** — 现用 `empty_response` 覆盖不可切换分支；`classify` 对 `ValueError` 亦返回 `unknown`/False，行为应对但未断言。
3. **重复查 provider** — `resolve_chain` 已解析 hops，router 循环内再次 `DramaLlmProvider.objects.filter(pk=...)`；可用 `provider_id=` 直写 FK 或缓存 hop 元数据微优化。
4. **弱 call-log 绑定边界** — 同 run 多条 log 时取 `-created_at` 最新一条；brief 允许弱关联，并发多 hop 成功时可能错绑（当前单线程 router 风险低）。

---

## Strengths

- 四测覆盖 brief 三例 + 成功路径 call-log FK；503 主备切换、中文耗尽摘要、终态不触第二跳均断言到位。
- `attempt_index` / `error_code` / `owner` / `v3_command_run` / `v3_project` 字段写入完整。
- 可注入 `chat_fn` 与 `config=hop.config` 传参对齐 `LlmProvider.chat_completion` 契约。
- 范围严格限定 Task 3，仓库内无 executor 引用 `chat_with_failover`。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 4 |

# P2-W1 Final Milestone Review — Failover 运行时 + Logs 尝试

**Reviewer:** whole-milestone gate (read-only)  
**Date:** 2026-07-23  
**Scope:** Spec P2-W1 only（§3–5、§6 Logs、§8.2 项 1/2/5；不含单价/rollup/`/usage`/ECharts）  
**Inputs:** acceptance baseline、plan、progress-p2-w1、p2w1-final-review-pkg、任务 reviews、关键集成源码  
**Verdict:** **Ready with minors**

---

## Spec / acceptance compliance

| # | 标准 | 结果 | 证据 |
|---|------|------|------|
| 1 | 主挂备通：同 run ≥2 attempt + 产物成功 | ✅ | `test_v3_llm_router` / `test_v3_failover_executor`；baseline ☑ |
| 2 | 链耗尽失败且 attempt 全记录 | ✅ | `test_exhausted_chain_raises_with_zh_summary` |
| 3 | 试连不走备选链 / 不写 attempt | ✅ | `provider_test` 直连；`test_connectivity_does_not_create_failover_attempts` |
| 4 | Logs API/UI「切换尝试」 | ✅ | `logs_views._serialize_failover_attempt`；`LogsPage` `FailoverAttemptsSection` |
| 5 | 无 ECharts/Usage/单价；legacy 净 | ✅ | baseline grep + `test_v3_legacy_gone` |
| — | `backup_provider_ids` + `V3FailoverAttempt` | ✅ | models + migration 0020；Models API PUT/GET |
| — | `failover_policy` / `llm_router` / executor 接入 | ✅ | resolve_chain + classify；`failover_call_scope` → `chat_with_failover` |

Task 7 机跑基线（53 backend / 8 LogsPage / typecheck）与 roadmap ✅ 勾选一致；本终审未重跑全量 `drama.tests`。

---

## Findings

### Critical
*(none)*

### Important

1. **空 `provider_id` hop 被静默跳过，env fallback 在生成路径失效** — `orchestrator/llm_router.py:91-93`  
   `resolve_chain` 无 active DB provider 时仍组装带 `LlmConfigService.resolve()`（可为 `source=env`）的 hop，但 `chat_with_failover` 对空 `provider_id` `continue`，从不 `invoke`。`execute_generation` 恒包 `failover_call_scope`，故无 active 行时生成落到「已尝试供应商：(无)」→ `_PROVIDER_HINT`，与 plan「无映射则单跳 active/**resolve**」及 phase-1 env 兜底不完全一致。DB 主备链验收路径不受影响；若仍承诺 env-only 开发/部署，应在 W1 收尾或 W2 早期修（空 id 时仍调用 `config`，或写 `skipped` 审计）。

### Minor

1. **§5 HTTP 403/408 缺单测** — 代码已在 `_SWITCHABLE_HTTP_STATUSES`；仅覆盖缺口。  
2. **异常链仅部分展开** — `_root_cause` 不扫描外层包装的 `LlmProviderError` HTTP 文案；当前 provider 直抛，风险低。  
3. **无映射双查 active** — `_single_hop_from_resolve` + `resolve()` 各查一次。  
4. **空链 / `(无)` 耗尽、ValueError 终态缺测** — 行为已有，断言不足。  
5. **router 内重复查 provider** — hop 已解析后再次 `filter(pk=…)`。  
6. **成功 attempt 弱绑定最新 call log** — 同 run 多 log 时可能错绑；单线程 router 风险低。  
7. **Spec §7「耗时」未建模** — API/UI 用 `created_at`；acceptance/plan Task 6 未要求 `latency_ms`。  
8. **Spec §4.1「启用」写校验未落** — PUT 只校验存在/≠主/去重/≤5（对齐 plan Task 5）；未拒 `is_enabled=False`。  
9. **`_config_from_provider` 恒 `enabled=True`** — 与既有 `resolve_for_role` 一致；链上禁用行不会以 `provider_disabled` 可切换失败，除非 chat 层另抛。

---

## Prior task minors triage

| 来源 | 项 | 处置 |
|------|----|------|
| T2 | 403/408 缺测 | **defer-to-W2**（补测即可；非功能洞） |
| T2 | nested cause / 双查 active | **defer-to-W2** |
| T3 | 空链/`(无)`、ValueError 缺测 | **defer-to-W2**（建议随 Important#1 同批补） |
| T3 | provider 再查、弱 call-log 绑定 | **defer-to-W2** |
| T3/T4 | 空 `provider_id` 不 invoke | **fix-now 优先**（见 Important#1）；若不修须在 W2 plan 显式声明「生成仅 DB provider」 |
| T6 | 无 attempt latency | **defer-to-W2**（可派生 call log `latency_ms` 或加字段；非 W1 门禁） |
| — | 写 API 启用校验；链上跳过 disabled | **defer-to-W2**（主备 UI/API 一并收紧） |

---

## Strengths

- 主备链、可切换/终态、耗尽中文摘要、executor 接入与试连隔离边界清晰。  
- Logs 契约（OpenAPI / TS / API / UI）对齐；无 Usage/ECharts/单价污染。  
- 任务级审查与 baseline 证据链完整；测试覆盖验收五项主路径。

---

## Residual risk

- Important#1 仅影响「无 active DB provider + env LLM」生成路径；产品化以 Models/角色映射为主时可接受为已知限制。  
- `SKIPPED` 状态已建模但未在缺失/跳过 hop 时写入，审计在极端空链下为空。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 1 |
| Minor | 9 |

**Verdict: Ready with minors** — P2-W1 验收标准满足，可进入 P2-W2；建议在 W2 开篇处理 Important#1（或文档冻结「生成仅 DB provider」）并捎带上表 defer 项。

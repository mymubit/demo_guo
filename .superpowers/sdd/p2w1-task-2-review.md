# P2-W1 Task 2 Review — failover_policy 链解析 + 错误可切换判定

**Reviewer:** task-scoped gate  
**Date:** 2026-07-23  
**Artifacts:** working tree (`failover_policy.py`, `test_v3_failover_policy.py`; `p2w1-task-2-review-pkg.md` 缺失，直接审读实现)  
**Verdict:** Spec ✅ · Code quality **Approved**

---

## Spec compliance: ✅

| Requirement | Result |
|-------------|--------|
| 仅 `orchestrator/failover_policy.py` + `test_v3_failover_policy.py`；无 llm_router / executor | ✅ |
| `ProviderHop` / `resolve_chain` / `classify_provider_error` 接口与 brief 一致 | ✅ |
| `resolve_chain`：主 + `backup_provider_ids` 去重保序；跳过不存在 id | ✅ |
| 无映射 / 空 role：单跳，配置等价 `LlmConfigService.resolve()` + active 元数据 | ✅ |
| 映射级 `temperature` / `max_tokens` 作用于整链 | ✅ |
| 复用 `ResolvedLlmConfig`；`_config_from_provider` 对齐 `resolve_for_role` 构造逻辑 | ✅ |
| Spec §5 可切换：timeout、连接、401/403/408/429/5xx、禁用/配置不全 | ✅ |
| 未知 / 业务类错误默认 `unknown`, False | ✅ |
| `LLM 流式响应为空`、HTTP 400 不可切换 | ✅ |
| HTTP / 禁用 / 配置文案与 `llm_provider.py` 前缀对齐 | ✅ |
| 单测模块 15 case；独立复跑 OK | ✅ |

**Scope note:** 全链 provider 缺失时回退 `_single_hop_from_resolve()` 未在 brief 写明，行为合理且与 report 自述一致；router 层需处理空 `provider_id` 单跳。

---

## Code quality: Approved

结构清晰：链解析与分类分离；HTTP 状态集中 `_http_error_code`；辅助函数命名与项目风格一致。TDD RED→GREEN 有 report 证据且复验通过。无 scope creep。

---

## Findings

### Critical
*(none)*

### Important
*(none)*

### Minor
1. **§5 边界 HTTP 缺单测** — 403/408 已在 `_SWITCHABLE_HTTP_STATUSES` 中处理，但无对应 test（401/429/5xx 已覆盖）。
2. **异常链仅部分展开** — `_root_cause` 用于 `TimeoutError` / `ConnectionError` 类型判定；若外层包装、内层为 `LlmProviderError`（含 `LLM HTTP …`），可能落 `unknown`/False。当前 `llm_provider` 直接 raise，风险低；router 集成前可加 `__cause__` 链扫描或补测。
3. **无映射路径双查 active** — `_single_hop_from_resolve` 先 `_active_provider()` 再 `LlmConfigService.resolve()` 各查一次 DB；可接受，后续可微优化。

---

## Strengths

- 15 测覆盖 brief 三例 + §5 主路径（429/401/5xx/400/empty/disabled/misconfigured/wrapped timeout）。
- `_config_from_provider` 与 `resolve_for_role` 的 temperature/max_tokens 回退语义一致。
- `classify_provider_error` 对 `LlmProviderError` 消息匹配与 `llm_provider.py` 抛错格式对齐。
- 范围严格限定 Task 2，无 router/executor 改动。

---

## Finding counts

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Important | 0 |
| Minor | 3 |

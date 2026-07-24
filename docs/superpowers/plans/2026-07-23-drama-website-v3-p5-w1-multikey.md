# P5-W1 Multi-Key Implementation Plan

Continuous SDD; no human gate.

## Task bundle (one implementer may do all)

1. Model `V3LlmProviderKey` + migration 0024+
2. `orchestrator/provider_keys.py`: `iter_api_keys(provider) -> list[str]` (primary then extras)
3. Update `llm_router.chat_with_failover`: for each hop, try each key by cloning ResolvedLlmConfig with that api_key; on switchable fail try next key; if all keys fail continue to next hop as today. Attempt rows: same provider, note error_code; optional error_message includes key label not raw key.
4. API nested keys under providers; never return plaintext key
5. ModelsPage UI manage extra keys
6. Tests: test_v3_provider_keys.py + router test multi-key failover
7. Baseline p5-w1; then auto P5-W2

## Status

✅ complete（2026-07-23）— report: `.superpowers/sdd/p5w1-report.md`

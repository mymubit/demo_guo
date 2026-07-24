### Task 2: V3UsageDailyRollup + increment helper

**Files:** `models.py` + same or `0022` migration；Create `orchestrator/usage_rollup.py`；Test `test_v3_usage_rollup.py`

**Produces:**
```python
def shanghai_date(dt) -> date: ...
def estimate_cost(*, provider_id, model_name, prompt_tokens, completion_tokens) -> Decimal | None: ...
def apply_call_to_rollup(call_log: DramaLlmCallLog) -> None:
    """按 Asia/Shanghai 日 + owner/project/command_type/model/provider 维度 upsert 累加。
    无单价：estimated_cost 不加，unpriced_call_count += 1。
    command_type 从 call.v3_command_run.command_type 取（可空）。
    provider_id：能从 base_url/model 反查则填，否则空。
    """
```

Wire: after `DramaLlmCallLog` create/save in `llm_call_log_service` (or equivalent single write path), call `apply_call_to_rollup`. Keep sync (no Celery required for W2).

- [ ] TDD: priced call increments cost；unpriced increments unpriced_call_count；same-day upsert
- [ ] Implement
- [ ] Commit 跳过

---

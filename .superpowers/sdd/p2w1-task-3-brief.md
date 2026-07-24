### Task 3: llm_router — 按链调用并写 FailoverAttempt

**Files:**
- Create: `backend/apps/drama/orchestrator/llm_router.py`
- Test: `backend/apps/drama/tests/test_v3_llm_router.py`

**Interfaces:**
- Consumes: `resolve_chain`, `classify_provider_error`, `LlmProvider.chat_completion`, `V3FailoverAttempt`
- Produces:
```python
def chat_with_failover(
    *,
    role_key: str,
    system_prompt: str,
    user_prompt: str,
    owner,
    v3_command_run=None,
    v3_project=None,
    json_mode: bool = True,
    chat_fn=None,  # 可注入，默认 LlmProvider.chat_completion
) -> dict:
    """返回与 LlmProvider.chat_completion 相同结构的 response dict。
    链耗尽时 raise LlmProviderError，message 含中文「已尝试供应商」与名称列表。
    """
```

每次 attempt：
1. `V3FailoverAttempt.objects.create(..., status` 可先 succeeded 路径直接写终态，或 create 后 update）
2. 调用 `chat_fn(..., config=hop.config)`
3. 成功：attempt=`succeeded`，若有 call log 关联则挂 FK（若 call log 由外层 `llm_call_scope` 写，router 内用 `DramaLlmCallLog.objects.filter(v3_command_run=...).order_by('-created_at').first()` 弱关联；**或** chat_fn 包装层返回 log id——优先：在已有 `llm_call_scope` 下调用，attempt 完成后绑定最新一条同 run 的 log）
4. 失败 + switchable：`failed_switchable`，继续
5. 失败 + not switchable：`failed_terminal`，raise
6. 耗尽：raise

- [ ] **Step 1: Write the failing test**

```python
@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class LlmRouterTests(TestCase):
    def test_failover_to_backup_on_switchable_error(self):
        # mapping 主=p1 备=p2；chat_fn 第一次 raise LlmProviderError("LLM HTTP 503")，第二次返回假 choices
        # resp = chat_with_failover(...)
        # attempts.count()==2；statuses == failed_switchable, succeeded

    def test_exhausted_chain_raises_with_zh_summary(self):
        # 两跳均 503；assertRaises；str(exc) 含「已尝试供应商」

    def test_terminal_error_stops_without_backup(self):
        # 第一跳 raise ValueError 或 classify 为不可切换的 LlmProviderError 文案
        # attempts==1 failed_terminal；不调用第二跳
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `llm_router.py`**

- [ ] **Step 4: Run — expect OK**

- [ ] **Step 5: Commit** — 跳过

---

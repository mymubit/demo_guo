### Task 4: executor 接入 router；试连不走链

**Files:**
- Modify: `backend/apps/drama/skills_bridge/executor.py`（`_default_llm_call`）
- Modify: `backend/apps/drama/orchestrator/provider_test.py`（确认仍直连指定 provider，**不**调用 `chat_with_failover`）
- Test: `backend/apps/drama/tests/test_v3_failover_executor.py`
- Modify if needed: 现有 `test_v3_provider_test.py`（断言试连 attempt 数为 0 或不存在 failover 行）

**Interfaces:**
- Consumes: `chat_with_failover`
- Produces: `_default_llm_call` 经 router；需传入 `owner`/`run`/`project`——从 `execute_generation` 已有参数闭包注入（改 `_default_llm_call` 签名或用 contextvars）

推荐：**contextvars** 在 `execute_generation` 入口 set `FailoverCallContext(owner, run, project)`，`_default_llm_call` 读取；避免大面积改 `llm_call` 回调签名。测试用注入 `llm_call=` 仍绕过 router（保持现有单测）；另增测例用 mock `chat_fn` 挂在 router 层。

更稳妥最小改动：
```python
def _default_llm_call(prompt: str, *, role: str = "") -> str:
    from apps.drama.orchestrator.llm_router import chat_with_failover
    ctx = get_failover_call_context()  # 无则 fallback 旧逻辑单跳
    response = chat_with_failover(
        role_key=role or "",
        system_prompt="你是短剧创作助手，只输出合法 JSON。",
        user_prompt=prompt,
        owner=ctx.owner,
        v3_command_run=ctx.run,
        v3_project=ctx.project,
    )
    ...
```

- [ ] **Step 1: Write failing integration test**

`test_v3_failover_executor.py`：seed 项目 + mapping 双 provider；patch `LlmProvider.chat_completion` 侧或 router `chat_fn` 使第一跳失败第二跳返回合法 quality/topic JSON；跑 `execute_generation` 一个轻量命令（如已有 fixture 的 `score_quality` 或 `generate_topic_brief`）；断言 `V3FailoverAttempt` ≥2 且产物写入。

另：`test_connectivity_does_not_create_failover_attempts` — 跑现有试连路径，`V3FailoverAttempt.objects.count()==0`。

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Wire executor + verify provider_test untouched by router**

- [ ] **Step 4: Run failover executor + provider_test — expect OK**

- [ ] **Step 5: Commit** — 跳过

---

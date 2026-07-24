### Task 3: executor 支持分集/正文 JSON 形态

**Files:**
- Modify: `skills_bridge/executor.py`
- Test: extend skills_bridge / 新 `test_v3_episode_executor.py`

**约定（mock LLM 返回）：**
- `generate_episode_plan` / `revise_episode_plan`：单对象 = `episode_plan` payload  
- `write_episode_batch`：

```json
{
  "episode_scripts": { "episodes": [ ... ] },
  "memory_checkpoint": { ... }
}
```

`revise_episode_plan`：executor 将 LLM 返回的局部 episodes **合并**进已有 committed plan 的拷贝后再 validate（合并逻辑单测覆盖：范围外卡片不变）。

- [ ] **Step 1–4: fake llm_call TDD 至 PASS**

---


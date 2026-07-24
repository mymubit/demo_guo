### Task 4: 编排 live 命令 + confirm_episode_plan / confirm_script_candidate

**Files:**
- Modify: `orchestrator/types.py`、`dispatcher.py`、`confirm.py`、`async_runner.py`
- Test: `test_v3_episodes_async.py`

**语义：**
- `generate_episode_plan`：无 committed 蓝图（至少 `story_bible`+`project_brief`，推荐检查 blueprint 五件已确认或 `stage in (episodes,writing,...)`）→ failed 人话
- `confirm_episode_plan`：supersede 旧 candidate；`stage=writing`（仅当当前为 episodes）
- `write_episode_batch`：校验 `episode_range`；缺分集计划 → failed
- `confirm_script_candidate`：提交 `episode_scripts`（及同 run 的 `memory_checkpoint`）；supersede 旧候选
- 继续使用 `V3_LLM_CALL_OVERRIDE` + eager

- [ ] **Step 1: 测试用例**
  1. 无蓝图生成分集 → failed  
  2. 有蓝图 → generate plan → confirm → stage writing  
  3. revise 仅改 ep 2 → 其它集不变  
  4. write 1–2 → 两产物 candidate  
  5. confirm scripts → committed  
  6. 双 generate plan → confirm 后无残留 candidate（回归 supersede）

- [ ] **Step 2–4: 实现 PASS**

---


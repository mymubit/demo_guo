### Task 2: recipe_map + fixtures + validate 覆盖

**Files:**
- Modify: `skills_bridge/recipe_map.py`
- Create fixtures for `episode_plan`、`episode_scripts`、`memory_checkpoint`（最小合法 JSON，对齐 schema）
- Extend: `test_v3_skills_bridge.py`

**Interfaces:**

```python
"generate_episode_plan": {
  "recipe_id": "design-episode-plan",
  "role": "drama-episode-designer",
  "writes": ["episode_plan"],
  "requires_committed": ["project_brief", "story_bible"],  # 至少 brief+bible；实现时可要求蓝图五件套中的 bible
},
"revise_episode_plan": {
  "recipe_id": "revise-episode-plan",
  "role": "drama-episode-designer",
  "writes": ["episode_plan"],
  "requires_committed": ["episode_plan"],
},
"write_episode_batch": {
  "recipe_id": "write-episodes",
  "role": "drama-script-writer",
  "writes": ["episode_scripts", "memory_checkpoint"],
  "requires_committed": ["episode_plan", "story_bible", "project_brief"],
},
```

- [ ] **Step 1–4: TDD** — `recipe_for` 断言；fixture 通过 `validate_artifact_payload`

**依赖检查：** 扩展 `executor._ensure_committed_dependencies` 读取 recipe 的 `requires_committed`（若尚硬编码则改为读 recipe）。

---


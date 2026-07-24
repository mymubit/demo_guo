### Task 2: `skills_bridge` 配方映射 + 校验（无 LLM）

**Files:**
- Create: `backend/apps/drama/skills_bridge/__init__.py`
- Create: `backend/apps/drama/skills_bridge/recipe_map.py`
- Create: `backend/apps/drama/skills_bridge/validate.py`
- Test: `backend/apps/drama/tests/test_v3_skills_bridge.py`
- Fixture: `backend/apps/drama/tests/fixtures/v3_project_brief_candidate.json`（从 `drama-skills/schemas/artifacts/project_brief/1.schema.json` 构造最小合法样例；可先用精简必填字段）

**Interfaces:**
- Produces:

```python
# recipe_map.py
COMMAND_RECIPES: dict[str, dict] = {
  "generate_topic_brief": {
    "recipe_id": "create-project-brief",  # 内部 only
    "role": "drama-topic-director",
    "writes": ["project_brief"],
  },
  "generate_blueprint": {
    "recipe_id": "compose-story-bible",
    "role": "drama-story-bible",
    "writes": [
      "story_bible", "character_system", "world_system",
      "emotion_system", "originality_report",
    ],
  },
}

def recipe_for(command_type: str) -> dict: ...
```

```python
# validate.py
def validate_artifact_payload(artifact_key: str, payload: dict) -> list[str]:
    """返回错误列表；空列表表示通过。优先用 skills_loader / jsonschema 对齐仓库现有校验方式。"""
```

- [ ] **Step 1: 测试** — `recipe_for("generate_topic_brief")["writes"] == ["project_brief"]`；非法 payload 返回非空错误；fixture 合法 payload 通过

- [ ] **Step 2–4: TDD 实现至 PASS** — 实现时阅读 `apps.drama.services.skills_loader` 现有 API，**不要**新造第二套 schema 路径

---


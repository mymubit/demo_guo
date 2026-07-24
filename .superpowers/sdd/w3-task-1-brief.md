### Task 1: 契约扩展 + `V3ScriptDraft`

**Files:**
- Modify: `docs/contracts/v3/commands.md`、`frontend/src/types/v3/commands.ts`、`api.test.ts`（枚举含新命令）
- Modify: `models.py` + migration
- Test: `test_v3_script_draft.py`

**Interfaces — ScriptDraft:**

```python
class V3ScriptDraft(models.Model):
    id = UUID PK
    project = FK V3Project
    episode_number = PositiveIntegerField
    payload = JSONField  # {scenes: [{id, heading, beats:[{type, text, character?}]}]}
    updated_at = auto_now
    Meta: unique (project, episode_number)
```

- [ ] **Step 1: 失败测试** — 缺模型；commands 枚举缺 `confirm_episode_plan`

- [ ] **Step 2–4: 实现至 PASS**；`PRODUCT_COMMAND_TYPES` 增加 `confirm_episode_plan`

---


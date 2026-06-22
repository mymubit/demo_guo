# 版本与灰度发布

---

## 1. 目标

Skill/Agent/Prompt 多版本并存时的发布、分流与回滚策略。

## 2. 版本标识

| 对象 | 版本字段 |
|------|----------|
| SkillRuleItem | `version_tag`（如 v5.2.0） |
| SkillRuleConfig | `version_tag` |
| AgentSkillDefinition | `version` + lifecycle |
| AgentPromptVersion | `version`（每 Agent 多行） |
| AgentDefinition | `version`（定义级） |

## 3. AgentSkillDefinition 灰度

条件：`lifecycle_status=gray`

```python
def pick_skill_version(skill_id: str, user_id: int) -> AgentSkillDefinition:
    bucket = int(hashlib.md5(f"{salt}{user_id}".encode()).hexdigest(), 16) % 100
    gray = AgentSkillDefinition.objects.filter(skill_id=skill_id, lifecycle_status="gray").first()
    active = AgentSkillDefinition.objects.filter(skill_id=skill_id, lifecycle_status="active").first()
    if gray and bucket < gray.gray_weight:
        return gray
    return active
```

| gray_weight | 含义 |
|-------------|------|
| 100 | 全量灰度版 |
| 0 | 永不命中灰度 |
| 30 | 约 30% 用户实验版 |

同一 user_id 稳定命中同一版本（salt 不变）。

## 4. AgentPromptVersion 发布

- 仅一条 `is_active=true`（DB UniqueConstraint）
- 发布新版本：create → set active → 旧版 is_active=false
- 回滚：将旧 version 重新设为 active

C 端 run 记录 `prompt_version` 便于追溯。

## 5. SkillRuleItem 发布

- 同 `rule_key` 仅一条 active
- A/B：可有两条不同 rule_key 的 draft 实验，approve 时选择保留哪条 key
- 回滚：archived 行 re-approve（需运营确认）

## 6. 与 C 端用户一致性

| 类型 | 分流键 |
|------|--------|
| AgentSkill gray | user_id |
| Agent Prompt | 无灰度（全量切换 active） |
| SkillRuleItem | 无用户级灰度（全站 active） |

若需 Prompt 灰度：复制 Agent 为 `agent_id_v2` + workspace 隐藏/入口 Plan 分流（见 [33-ENTRY-PLAN-ROUTING.md](./33-ENTRY-PLAN-ROUTING.md)）。

## 7. 回滚 Runbook

| 事件 | 动作 | RTO |
|------|------|-----|
| 新 Prompt 质量差 | 旧 PromptVersion 设 active | < 5 min |
| 新 Rule Item 误伤 | archive active，恢复 archived | < 5 min |
| gray 实验失败 | gray_weight=0 或 lifecycle=deprecated | 即时 |

## 8. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | 切换 active prompt 后新 run 用新版 |
| boundary | gray_weight=100 全员 gray 版 |
| error | 无 active Prompt 时 Agent unhealthy |
| permission | 仅 staff 可 approve Item |

## 9. 旧逻辑删除

- Fusion 节点 skill 版本绑文件 — 删除
- 文件 runner 多版本并存 — 删除

参考：[12-AGENT-SKILL-DEFINITION-SPEC.md](./12-AGENT-SKILL-DEFINITION-SPEC.md)。

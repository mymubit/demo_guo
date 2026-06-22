# Project 上下文记忆

---

## 1. 目标

用户反复修改同一项目时，Agent 感知历史拒绝与风格偏好（PDF 借鉴 #3）。

> **状态**：`Project.agent_notes` + PATCH API + FIFO 截断已实现。

在 `Project` 增加：

```python
agent_notes = models.JSONField(default=dict, blank=True)
```

建议结构：

```json
{
  "rejects": ["第2版大纲太狗血", "第1集悬念不够"],
  "style_preferences": ["快节奏", "反转多"],
  "character_guidance": "主角内心戏要足，对白要狠",
  "last_feedback_at": "2026-06-19T10:00:00Z"
}
```

**禁止**存敏感 PII；**禁止**无限增长 — 每 key 最多 N 条（如 rejects 20 条 FIFO）。

## 3. 写入时机

| 事件 | 动作 |
|------|------|
| 用户拒绝/撤销某 Artifact 版本 | append rejects + artifact_key |
| 工作台「风格备注」提交 | 更新 style_preferences / character_guidance |
| Run 失败用户填写原因 | 可选 append |

API：`PATCH/GET /api/creation/projects/<id>/agent-notes/`（`views_stream.ProjectAgentNotesView`）。

## 4. 注入点

`IndependentAgentService.build_agent_input()` 返回：

```python
payload["agent_notes"] = project.agent_notes or {}
```

`user_prompt_template` 增加可选块：

```text
{% if agent_notes.rejects %}
用户曾拒绝以下方向，请勿重复：
{{ agent_notes.rejects }}
{% endif %}
```

或使用 `_render_template` 路径 `{{ params.agent_notes }}` 由 params 传入。

## 5. 与 ReferenceMaterial 区别

| | agent_notes | ReferenceMaterial |
|---|-------------|-------------------|
| 来源 | 用户行为 | 上传素材 |
| 生命周期 | 项目级 | 项目级 injection |
| 大小 | 小文本 | 大文件解析 |

## 6. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | notes 出现在 rendered user_prompt |
| boundary | rejects 超上限截断 |
| error | 非法 JSON patch 400 |
| permission | 非 owner 不可写 notes |

## 7. 旧逻辑删除

Fusion upstream 无记忆的多节点传递 — 由 Artifact + agent_notes 取代。

参考：[30-INDEPENDENT-AGENT-RUNTIME.md](./30-INDEPENDENT-AGENT-RUNTIME.md)、[01-AGENT-SKILL-USER-LAYERS.md](./01-AGENT-SKILL-USER-LAYERS.md)。

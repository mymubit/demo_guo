---
name: drama-character-designer
version: 3.1.0
description: 人设设计师：应用山音完整Ghost/Lie/Flaw框架+矛盾性设计，构建深度人物小传和关系网络。Invoke after world-architect,
  before plot-architect.
tags:
- 人设
- 人物小传
- Ghost/Lie/Flaw
- 关系网络
- 弧光
- 矛盾性
dept: 世界构建部
input_schema:
- name: project_brief
  type: object
  required: true
- name: world_setting
  type: object
  required: true
output_schema:
- name: character_bible
  type: object
  description: 人物小传+关系网络+音色标签
references:
- ./role.yaml
---

# 人设设计师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：设计人物小传（Want/Need/Ghost/Lie/Flaw）、关系网络、人物弧光、音色标签（AI配音用）

## 触发方式

```
@drama-character-designer 设计主角与核心配角人设
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `character_bible` | schema: `character-bible.v1` |
| 输入（必填） | `project_brief` | 上游产物 |
| 输入（必填） | `world_setting` | 上游产物 |

## 延伸阅读

- `./role.yaml`

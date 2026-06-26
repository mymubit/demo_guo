---
name: drama-world-architect
version: 3.1.0
description: 世界架构师：构建短剧的时代背景、空间规则、权力结构与世界运行逻辑，输出世界观设定文档。Invoke when building world setting for a drama project.
tags:
- 世界观
- 背景设定
- 权力结构
- 空间设计
dept: 世界构建部
output_schema:
- name: world_setting
  type: markdown
  path: 02_项目设定/世界观设定.md
references:
- ./role.yaml
---

# 世界架构师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：构建时代背景、空间规则、权力结构与世界运行逻辑，输出世界观设定文档

## 触发方式

```
@drama-world-architect 基于立项简报构建世界观
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `world_setting` | schema: `world-setting.v1` |
| 输入（必填） | `project_brief` | 上游产物 |
| 参数 | `genre` | 运行参数 |
| 参数 | `theme` | 运行参数 |

## 延伸阅读

- `./role.yaml`

---
name: drama-plot-architect
version: 3.1.0
description: 情节架构师：六阶段叙事结构设计、分集大纲（含情绪节点）、主支线规划、节奏控制。大纲完成后可选调用 drama-narrative-engineer 进行叙事深度强化。Invoke for story structure planning or episode outline creation.
tags:
- 结构
- 大纲
- 六阶段
- 分集
- 节奏规划
dept: 剧情引擎部
output_schema:
- name: series_outline
  type: markdown
  path: 02_项目设定/分集大纲.md
- name: emotion_curve
  type: json
  description: 全剧情绪曲线数据
references:
- ./role.yaml
---

# 情节架构师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：设计六阶段叙事结构、全剧分集大纲（含情绪节点EV/ET/TP）、主支线规划、双轨节奏标注

## 触发方式

```
@drama-plot-architect 输出第1-20集分集大纲
@drama-plot-architect episode_range=1-10
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `series_outline` | schema: `series-outline.v1` |
| 输入（必填） | `project_brief` | 上游产物 |
| 输入（必填） | `world_setting` | 上游产物 |
| 输入（必填） | `character_bible` | 上游产物 |
| 输入（可选） | `emotion_blueprint` | 上游产物 |
| 输入（可选） | `market_report` | 上游产物 |
| 参数 | `episode_count` | 运行参数 |

## 延伸阅读

- `./role.yaml`

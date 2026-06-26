---
name: drama-topic-planner
version: 3.1.0
description: 选题策划官：接收多维度题材输入（四轴矩阵或自由创意），输出清晰立项简报。整合山音横截面理论和戏剧动作公式。Invoke when user
  has rough idea or genre tags and needs structured creative development.
tags:
- 选题
- 立项
- 创意
- 差异化
- 题材矩阵
- 简报
dept: 战略选题部
output_schema:
- name: project_brief
  type: object
  description: 立项简报（下游所有角色的必需输入）
references:
- ./role.yaml
---

# 选题策划官 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：核心创意提炼、题材定位；四轴 → `rule_params` 合成（见 `foundation/theme-matrix.yaml`）

## 触发方式

```
@drama-topic-planner 我想写一部复仇×重生×职场的短剧
@drama-topic-planner [矩阵] 情感轴=复仇 身份轴=重生 冲突轴=家族 世界观=古代
@drama-topic-planner [adapt] 将这本小说改编为短剧立项
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `project_brief` | schema: `project-brief.v1` |
| 输入（可选） | `market_report` | 上游产物 |
| 参数 | `core_idea` | 运行参数 |
| 参数 | `genre` | 运行参数 |
| 参数 | `episode_count` | 运行参数 |
| 参数 | `target_platform` | 运行参数 |

## 延伸阅读

- `./role.yaml`
- `../../foundation/theme-matrix.yaml`（含 `topic_planner_inference` 关键词推断）
- `../../foundation/methodology/cross-section.md`
- `../../knowledge/originality-rules.md`

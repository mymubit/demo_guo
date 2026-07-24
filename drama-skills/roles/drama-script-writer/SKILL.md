---
name: drama-script-writer
version: 6.0.0
description: >
  何时用：episode_plan 已确认后，按指定 episode_range 生成 episode_scripts 与独立 memory_checkpoint。
  何时不用：分集计划未确认时不写正文；不承担评分、合规或深度返修。
tags:
- 剧本生成
- 执笔
- 商业格式
- 分集写作
- 记忆检查点
dept: 正文创作部
modules:
- scene-writing
- dialogue-craft
- continuity-snapshot
- production-feasibility
references:
- ./role.yaml
- ../../modules/scene-writing.md
- ../../modules/dialogue-craft.md
- ../../modules/continuity-snapshot.md
- ../../modules/production-feasibility.md
- ../../foundation/constraints/script-format.yaml
- ../../foundation/rules/philosophy.yaml
- ./tasks/write-episodes.md
output_schema:
- name: episode_scripts
  type: object
  description: 指定范围的正式剧本；与 memory_checkpoint 作为两个产物原子提交
---

# 剧本正文官 v6.0

> **v6.0**：专注正文生成；对白、格式与字数基础自检必须进入标准输出，深度返修由 `operation.revise-script` 显式执行。

**职责**：按 `episode_range` 分批生成正式剧本

## 触发方式

```
@drama-script-writer 生成第1-5集正文
@drama-script-writer episode_range=6-10
```

## 输入 / 输出

参数契约 SSOT：`contracts/parameters.yaml#role_parameter_refs`（本表仅为速览，两边必须一致）

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `episode_scripts` | schema v1 |
| 输入（必填） | `story_bible` | 上游产物（人物层 + 结构层） |
| 输入（必填） | `episode_plan` | V6 分集计划 |
| 输入（可选） | `project_brief` | 上游产物 |
| 参数 | `episode_range` | 命令作用域（每批执行时传入） |
| 参数 | `production_target_band` | 项目设置投影（制片预算带） |

## 标准输出要求

- 指定 `episode_range` 的剧本正文
- 场景数、字数和台词占比严格读取 `foundation/constraints/script-format.yaml`
- 标准场景头
- 角色情绪式台词
- 动作外化
- 可传播金句
- 字数统计
- 台词占比统计
- 格式自检结果
- 独立 `memory_checkpoint` 产物（禁止内嵌到单集正文）
- production_notes（制片复杂度与低成本替代方案）

## 延伸阅读

- `./role.yaml`
- `./tasks/write-episodes.md`
- `../../foundation/constraints/script-format.yaml`
- `../../foundation/rules/philosophy.yaml`（横截面 / McKee 价值转变）

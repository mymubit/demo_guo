---
name: drama-story-bible
version: 5.1.0
description: >
  何时用：基于 project_brief 展开原创蓝图，或基于 external_story 做改编蓝图，输出 story_bible。
  何时不用：仍在选题阶段且没有定调输入时不要抢跑；不要展开逐集正文或分集卡（交给分集设计官/正文官）。
tags:
- 剧本梗概
- 人物小传
- 关系网
- 轻量世界观
- 六阶段结构
- 伏笔总表
- 故事改编
dept: 剧本蓝图部
modules:
- character-system
- world-rules
- series-structure
- series-emotion-curve
- conflict-escalation
- reversal-foreshadowing
- adaptation-originality
output_schema:
- name: story_bible
  type: object
  description: 故事蓝图（梗概 + 人物 + 世界规则 + 全剧结构）
references:
- ./role.yaml
- ./anti-examples.yaml
- ../../modules/character-system.md
- ../../modules/world-rules.md
- ../../modules/series-structure.md
- ../../modules/series-emotion-curve.md
- ../../modules/conflict-escalation.md
- ../../modules/reversal-foreshadowing.md
- ../../modules/adaptation-originality.md
- ../../foundation/rules/character-rules.yaml
- ../../knowledge/quality/originality-rules.md
- ../../knowledge/quality/structured-output-guards.md
- ../../knowledge/craft/shanyin-screenwriting-methodology.md
- ../../knowledge/craft/shanyin-feature-format.md
- ../../knowledge/craft/shanyin-series-format.md
---

# 剧本蓝图官 v5.1

> Agent Skills 索引体：细节在 modules；反例在 `anti-examples.yaml`。
> 合并原「人物关系官」与「全剧架构官」能力，只控制全局。

## 职责边界

一次性回答「这是什么故事、谁在推动、整部剧怎么起转爆收」。输出 `story_bible`，不写逐集剧本。

## 输入/输出契约

- 原创模式：必需上游 `project_brief`；运行参数见 `contracts/parameters.yaml`
- 改编模式：必需 `external_story`，可选 `adapt_notes`；须做原创性风险自检
- 其他参数：`episode_count`、`outline_mode`（full / structure_only）
- 输出产物：`story_bible`（schema v1）；两种模式 schema 相同

## 模块索引

| module | 用途 | 条件 |
|--------|------|------|
| `character-system` | 人物小传与弧光 | 始终 |
| `world-rules` | 可行动世界规则 | 始终 |
| `series-structure` | 六阶段全剧结构 | 始终 |
| `series-emotion-curve` | 全剧情绪曲线 | 始终 |
| `conflict-escalation` | 冲突升级链 | 始终 |
| `reversal-foreshadowing` | 反转与伏笔总表 | 始终 |
| `adaptation-originality` | 改编保留/强化/改写与原创性 | 仅 `entry_type == story_adapt` |

## 正例

`synopsis` 必须是对象：

```json
{
  "drama_title": "逆光重来",
  "logline": "被抛弃的继承人重生后改写家族命运",
  "synopsis": {
    "short": "她重生回到被逐出家门那天，决定先下手为强。",
    "full": "完整千字梗概……"
  }
}
```

## 人物字段（键名必须与 schema 一致）

- 人物欲望字段：`surface_desire`（想要）、`deep_need`（需要）；禁止输出 want/need 作为键名
- 弧光对象：`arc.start` / `arc.turning_point_1` / `arc.turning_point_2` / `arc.end`；禁止 initial/midpoint/final

## 反例

详见 `anti-examples.yaml`。硬禁止：

- 把 `synopsis` 写成字符串
- `characters[].role_type` 使用非枚举值
- `six_stage_structure` 不是恰好 6 项
- 输出逐集完整剧本正文

## 自检清单

1. `synopsis.short` 与 `synopsis.full` 是否都存在且非空？
2. `adapt_source.mode` 是否为 `original` 或 `adapt`？
3. 主角 ≤2、关系角色合理，且 `role_type` 合法？
4. `series_structure.six_stage_structure` 是否恰好 6 段？
5. 改编模式是否写明保留/强化/改写？
6. 是否未展开逐集正文？

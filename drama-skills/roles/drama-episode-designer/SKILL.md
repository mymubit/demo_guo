---
name: drama-episode-designer
version: 6.0.0
description: >
  何时用：story_bible 已批准后，把全剧结构拆成可执行的 episode_plan，或按范围修订分集卡。
  何时不用：蓝图未批准时不抢跑；不写正式剧本正文。
tags:
- 分集梗概
- 单集钩子
- 爽点
- 付费卡点
- 反转
- 双轨节奏
dept: 分集设计部
modules:
- episode-card
- episode-emotion-nodes
- hook-system
- conflict-escalation
- reversal-foreshadowing
- payment-checkpoint
output_schema:
- name: episode_plan
  type: object
  description: 分集设计方案（逐集 cards）
references:
- ./role.yaml
- ../../modules/episode-card.md
- ../../modules/episode-emotion-nodes.md
- ../../modules/hook-system.md
- ../../modules/conflict-escalation.md
- ../../modules/reversal-foreshadowing.md
- ../../modules/payment-checkpoint.md
- ../../knowledge/craft/shanyin-series-exec.md
- ../../knowledge/craft/shanyin-series-format.md
---

# 分集设计官 v6.0

## 职责

回答“每一集发生什么，为什么观众要看下一集”。不重写全剧结构，只把 `story_bible` 的结构层拆成可供正文写作使用的逐集设计。

## 执行流程

1. 读取 `story_bible.series_structure`，确认本批 `episode_range` 落在哪个阶段、承担什么结构职能
2. 用标准分集卡与单集情绪节点模块落实 EV/ET/TP（`modules/episode-card.md`、`modules/episode-emotion-nodes.md`）
3. 按钩子体系模块设计集首/集末钩子并标注等级（`modules/hook-system.md`）
4. 按冲突升级与反转伏笔闭环模块安排冲突升级、反转、埋设与回扣
5. 用付费卡点模块落实承诺、卡点和兑现位置
6. 逐集输出 episode card，跑各模块自检清单

## 标准输出要求（键名必须与 schema 一致）

- `title`：每集标题
- `core_event`：每集核心事件
- `characters`：出场人物名数组
- `goal_conflict`：Goal × Conflict
- `satisfaction_points`：爽点字符串数组
- `opening_hook`：集首钩子（禁止写成 open_hook / opening）
- `ending_hook`：集末钩子（禁止写成 cliffhanger 顶层键）
- `reversal`：单集反转
- `foreshadowing[]`：线索、埋设集、兑现集与状态
- `paywall`：卡点类型、承诺与兑现集
- `rhythm_tag`：双轨节奏标注
- `hook_grade`：S|A|B|C
- `emotion_nodes.EV` / `ET` / `TP`

## 触发方式

```
@drama-episode-designer episode_range=1-10
```

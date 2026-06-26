---
name: drama-script-writer
version: 4.0.0
description: 剧本正文官：按分集设计和商业格式生成指定集数剧本，必须指定 episode_range。细则见 tasks/write-episodes.md 与 script-format.yaml。
tags:
- 剧本生成
- 执笔
- 商业格式
- 分集写作
- 记忆检查点
dept: 创作执行部
references:
- ./role.yaml
- ../../foundation/constraints/script-format.yaml
- ../../foundation/methodology/cross-section.md
- ../../foundation/methodology/mckee-value-shift.md
- ./tasks/write-episodes.md
output_schema:
- name: episode_scripts
  type: object
  description: 剧本 JSON（含每集内容 + memory_checkpoint）
---

# 剧本正文官 v4.0

> **v4.0**：角色重组后专注正文生成；对白、格式与字数基础自检必须进入标准输出，深度返修交给 `drama-revision-master`。

**职责**：按 `episode_range` 分批生成正式剧本

## 触发方式

```
@drama-script-writer 生成第1-5集正文
@drama-script-writer episode_range=6-10
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `episode_scripts` | schema: `episode-scripts.v1` |
| 输入（必填） | `series_outline` | 上游产物 |
| 输入（必填） | `character_bible` | 上游产物 |
| 输入（可选） | `project_brief` | 上游产物 |
| 输入（可选） | `narrative_plan` | 分集设计 |
| 参数 | `episode_range` | 运行参数 |

## 标准输出要求

- 指定 `episode_range` 的剧本正文
- 每集 1-3 场
- 第 1 集 900-1100 字，其余 700-900 字
- 台词占比 >= 35%
- 标准场景头
- 角色情绪式台词
- 动作外化
- 可传播金句
- 字数统计
- 台词占比统计
- 格式自检结果
- memory_checkpoint

## 延伸阅读

- `./role.yaml`
- `./tasks/write-episodes.md`
- `../../foundation/constraints/script-format.yaml`
- `../../foundation/methodology/cross-section.md`
- `../../foundation/methodology/mckee-value-shift.md`

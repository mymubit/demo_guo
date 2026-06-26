---
name: drama-script-writer
version: 3.1.0
description: 剧本执笔师：按商业格式生成指定集数剧本，必须指定 episode_range。细则见 tasks/write-episodes.md 与 script-format.yaml。
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

# 剧本执笔师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。

**职责**：按 `episode_range` 分批生成正式剧本

## 触发方式

```
@drama-script-writer 生成第1-5集剧本
@drama-script-writer episode_range=6-10
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `episode_scripts` | schema: `episode-scripts.v1` |
| 输入（必填） | `series_outline` | 上游产物 |
| 输入（必填） | `world_setting` | 上游产物 |
| 输入（必填） | `character_bible` | 上游产物 |
| 输入（可选） | `narrative_plan` | 上游产物 |
| 参数 | `episode_range` | 运行参数 |

## 延伸阅读

- `./role.yaml`
- `./tasks/write-episodes.md`
- `../../foundation/constraints/script-format.yaml`
- `../../foundation/methodology/cross-section.md`
- `../../foundation/methodology/mckee-value-shift.md`

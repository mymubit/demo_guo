---
name: drama-polish-master
version: 3.1.0
description: 精修大师：剧本完成后一站式精修（台词/格式/字数/分镜），输出 polished_script。
tags:
- 对白优化
- 修稿
- 格式规范
- 字数治理
- 分镜
dept: 修改润色部
modules:
- dialogue-polish
- format-fix
- word-count-governance
- storyboard-9col
output_schema:
- name: polished_script
  type: markdown
  description: 精修后的剧本+修改说明
references:
- ./role.yaml
- ../../modules/dialogue-polish.md
- ../../modules/format-fix.md
- ../../modules/word-count-governance.md
- ../../modules/storyboard-9col.md
---

# 精修大师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：剧本精修与格式治理（modules 见 frontmatter）

## 触发方式

```
@drama-polish-master 精修第1-5集剧本
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `polished_script` | schema: `polished-script.v1` |
| 输入（必填） | `episode_scripts` | 上游产物 |
| 输入（可选） | `review_report` | 上游产物 |
| 输入（可选） | `quality_report` | 上游产物 |
| 参数 | `episode_range` | 运行参数 |
| 参数 | `focus_areas` | 运行参数 |

## 延伸阅读

- `./role.yaml`
- `../../foundation/constraints/script-format.yaml`
- `../../modules/dialogue-polish.md`
- `../../modules/format-fix.md`
- `../../modules/word-count-governance.md`
- `../../modules/storyboard-9col.md`

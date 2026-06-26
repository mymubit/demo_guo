---
name: drama-production-pack
version: 3.1.0
description: 制作发行师：定稿后输出视觉/营销/交付物料，可选 Story-to-Game，输出 production_package。
tags:
- 视觉生产
- 分镜
- 营销
- 交付
- Story-to-Game
dept: 制作宣发部
modules:
- visual-anchor
- marketing-copy
- delivery-check
- story-to-game
output_schema:
- name: production_package
  type: object
  description: 完整制作发行物料包
references:
- ./role.yaml
- ../../modules/visual-anchor.md
- ../../modules/marketing-copy.md
- ../../modules/delivery-check.md
- ../../modules/story-to-game.md
---

# 制作发行师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：制作发行物料打包（modules 见 frontmatter）

## 触发方式

```
@drama-production-pack 输出制作发行包
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `production_package` | schema: `production-pack.v1` |
| 输入（必填） | `episode_scripts` | 上游产物 |
| 输入（必填） | `character_bible` | 上游产物 |
| 输入（可选） | `project_brief` | 上游产物 |
| 输入（可选） | `compliance_report` | 上游产物 |

## 延伸阅读

- `./role.yaml`
- `../../modules/visual-anchor.md`
- `../../modules/marketing-copy.md`
- `../../modules/delivery-check.md`
- `../../modules/story-to-game.md`

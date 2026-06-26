---
name: drama-narrative-engineer
version: 3.1.0
description: 叙事工程师：大纲完成后强化情绪、钩子、冲突、反转与节奏，输出 narrative_plan。
tags:
- 情绪蓝图
- 钩子设计
- 冲突体系
- 反转设计
- 双轨节奏
dept: 剧情引擎部
modules:
- emotion-blueprint
- hook-system
- conflict-escalation
- reversal-system
- psychology-immersion
output_schema:
- name: narrative_plan
  type: object
  description: 完整叙事增强方案（情绪蓝图+钩子+冲突+反转+节奏+心理）
references:
- ./role.yaml
- ../../modules/emotion-blueprint.md
- ../../modules/hook-system.md
- ../../modules/conflict-escalation.md
- ../../modules/reversal-system.md
- ../../modules/psychology-immersion.md
---

# 叙事工程师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：大纲后的叙事深度强化（modules 见 frontmatter）

## 触发方式

```
@drama-narrative-engineer 基于大纲输出叙事工程方案
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `narrative_plan` | schema: `narrative-plan.v1` |
| 输入（必填） | `series_outline` | 上游产物 |
| 输入（必填） | `character_bible` | 上游产物 |
| 输入（可选） | `project_brief` | 上游产物 |

## 延伸阅读

- `./role.yaml`
- `../../modules/emotion-blueprint.md`
- `../../modules/hook-system.md`
- `../../modules/conflict-escalation.md`
- `../../modules/reversal-system.md`
- `../../modules/psychology-immersion.md`

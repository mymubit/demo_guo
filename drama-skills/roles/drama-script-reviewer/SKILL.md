---
name: drama-script-reviewer
version: 3.1.0
description: 审稿官：执行四层系统性审查（格式合规+山音横截面+McKee价值转变+双轨节奏+逻辑一致性），输出详细审查报告和必修/建议清单。Invoke
  after script-writer to quality check the script.
tags:
- 审稿
- 格式检查
- McKee价值转变
- 横截面检验
- 双轨节奏
- 逻辑一致性
dept: 评审质控部
input_schema:
- name: episode_scripts
  type: object
  required: true
- name: episode_range
  type: string
  required: false
  description: 审查的集数范围
output_schema:
- name: review_report
  type: object
  description: 详细审查报告（格式/McKee/节奏/逻辑四层结果）
references:
- ./role.yaml
---

# 审稿官 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：剧本格式合规检查、结构完整性审查（六阶段/四段式）、人物逻辑一致性核查、McKee价值转变检验

## 触发方式

```
@drama-script-reviewer 审查第1-5集剧本
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `review_report` | schema: `review-report.v1` |
| 输入（必填） | `episode_scripts` | 上游产物 |

## 延伸阅读

- `./role.yaml`
- `../../foundation/constraints/script-format.yaml`

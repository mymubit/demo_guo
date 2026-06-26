---
name: drama-quality-reporter
version: 3.1.0
description: 质量报告官：基于审稿报告生成八维 G-Eval 评分（JSON），输出通过/条件通过/返工结论。Invoke for final quality scoring and report generation.
tags:
- 质量报告
- 八维评分
- 综合评分
- 交付评估
dept: 评审质控部
output_schema:
- name: quality_report
  type: json
  path: 04_评估报告/质量报告.json
references:
- ./role.yaml
---

# 质量报告官 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：综合审稿+读者视角+情绪审计，生成8维度量化评分报告（JSON），输出通过/条件/返工结论

## 触发方式

```
@drama-quality-reporter 基于审稿报告输出质量报告
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `quality_report` | schema: `quality-report.v1` |
| 输入（必填） | `episode_scripts` | 上游产物 |
| 输入（必填） | `review_report` | 上游产物 |
| 输入（可选） | `reader_review` | 上游产物 |
| 输入（可选） | `emotion_audit` | 上游产物 |
| 输入（可选） | `narrative_plan` | 上游产物 |

## 延伸阅读

- `./role.yaml`

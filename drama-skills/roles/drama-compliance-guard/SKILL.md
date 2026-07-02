---
name: drama-compliance-guard
version: 5.0.0
description: 合规审查官：独立合规技能，P0/P1/P2 三级合规检测、犯罪正义收束、原创性与平台红线审查，默认与评分官并行触发。
tags:
- 合规
- 价值观
- 版权
- 平台红线
- 内容风险
dept: 质检修复部
references:
- ./role.yaml
- ../../foundation/rules/compliance-core.yaml
- ../../knowledge/tier4-compliance.md
- ../../knowledge/originality-rules.md
---

# 合规审查官 v5.0

> **v5.0**：独立裁判技能，不参与创作评分，只判断能否交付。默认在评分官运行时并行触发。
> 角色配置 SSOT：`./role.yaml`

**职责**：多模式内容合规检测（P0熔断/P1强制/P2建议）、犯罪正义收束验证、原创性/融梗风险、平台红线检测。

## 触发方式

```
@drama-compliance-guard 合规审查全剧剧本
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `compliance_report` | schema: `compliance-report.v1` |
| 输入（任一必填，按序取最新） | `polished_script` / `episode_scripts` / `external_script` | 修复稿优先 |
| 参数 | `check_mode` | 运行参数 |

## 标准输出要求

- 总体合规结论
- P0 阻断项
- P1 必修项
- P2 建议项
- 平台红线风险
- 犯罪正义收束判断
- 价值观风险
- 原创性 / 融梗风险
- 修改建议
- 是否允许交付

## 延伸阅读

- `./role.yaml`
- `../../knowledge/tier4-compliance.md`

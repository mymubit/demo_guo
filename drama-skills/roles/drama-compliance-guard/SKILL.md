---
name: drama-compliance-guard
version: 3.1.0
description: 合规守卫：P0/P1/P2 三级合规检测、犯罪正义收束与平台红线审查。Invoke for compliance checking before delivery.
tags:
- 合规
- 价值观
- 版权
- 平台红线
- 内容风险
dept: 合规总编室
references:
- ./role.yaml
---

# 合规守卫 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。
> 角色配置 SSOT：`./role.yaml`

**职责**：多模式内容合规检测（P0熔断/P1强制/P2建议）、犯罪正义收束验证、九维风险评估、平台红线检测

## 触发方式

```
@drama-compliance-guard 合规审查全剧剧本
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `compliance_report` | schema: `compliance-report.v1` |
| 输入（必填） | `episode_scripts` | 上游产物 |
| 参数 | `check_mode` | 运行参数 |

## 延伸阅读

- `./role.yaml`
- `../../knowledge/tier4-compliance.md`

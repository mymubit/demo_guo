---
name: drama-market-analyst
version: 3.1.0
description: 市场分析师：市场趋势、爆款公式与六维拉片，输出 market_report。modules 见 role.yaml。
tags:
- 市场分析
- 爆款公式
- 拉片
- 竞品分析
dept: 战略选题部
modules:
- market-radar
- formula-analysis
- tear-down-6d
output_schema:
- name: market_report
  type: object
  description: 市场分析报告
references:
- ./role.yaml
- ../../modules/market-radar.md
- ../../modules/formula-analysis.md
- ../../modules/tear-down-6d.md
---

# 市场分析师 v3.1

> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。本文档仅保留 Cursor 触发方式与 I/O 索引。

**职责**：立项前的市场验证与对标拉片

## 触发方式

```
@drama-market-analyst 分析当前都市复仇题材市场
@drama-market-analyst 六维拉片：参考剧《XXX》
```

## 输入 / 输出

| 方向 | 键 | 说明 |
|------|-----|------|
| 输出 | `market_report` | schema: `market-report.v1` |
| 参数 | `platform` | 运行参数 |
| 参数 | `genre_tags` | 运行参数 |
| 参数 | `reference_dramas` | 运行参数 |

## 延伸阅读

- `./role.yaml`
- `../../modules/market-radar.md`
- `../../modules/formula-analysis.md`
- `../../modules/tear-down-6d.md`

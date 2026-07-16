---
name: drama-delivery-tool
version: 5.0.0
description: 宣发交付工具：吸收制作发行能力，输出 production_package。
tags:
- 宣发
- 交付
- 视觉提示词
- 投流文案
- 分镜摘要
- 互动改编
dept: 宣发交付部
modules:
- storyboard-9col
- visual-anchor
- marketing-copy
- delivery-check
- story-to-game
- budget-estimator
- platform-ops-checklist
output_schema:
- name: production_package
  type: object
  description: 宣发交付包
references:
- ./role.yaml
- ../../modules/storyboard-9col.md
- ../../modules/visual-anchor.md
- ../../modules/marketing-copy.md
- ../../modules/delivery-check.md
- ../../modules/story-to-game.md
- ../../modules/budget-estimator.md
- ../../modules/platform-ops-checklist.md
- ../../knowledge/production/story-to-game.md
- ../../knowledge/production/shanyin-director-methodology.md
- ../../knowledge/production/shanyin-director-styles.md
---

# 宣发交付工具 v5.0

## 职责

这是可选工具，不进入默认创作完成率。用于把终稿转成制作、预算、上架、宣发或互动改编物料。

运行参数（SSOT：`contracts/parameters.yaml#role_parameter_refs`）：
`deliverables`（交付项多选：storyboard/visual/marketing/interactive/budget/release）、
`target_platform`（上架清单平台）、`production_context`（制片带/地区/币种等上下文）。

## 执行流程

1. **先跑交付门禁**：评分达到当前 `scoring_preset` 的 pass_threshold 且该预设 `delivery_eligible=true`、合规通过且剧本完整
2. 汇总制片标签，输出复杂度/预算带与低成本替代方案
3. 生成九列分镜、视觉物料与营销文案
4. 按需生成互动改编，并执行平台上架清单
5. 组装 `production_package` 并附核验表

## 标准输出要求

- 剧名备选
- 海报 / 封面视觉提示词
- 主角视觉锚点
- 平台标题
- 简介
- 投流短文案
- 高光切片建议
- 制片复杂度与预算带
- 平台上架清单
- 交付完整性检查
- 互动改编可能性

## 触发方式

```
@drama-delivery-tool 生成宣发交付包
```

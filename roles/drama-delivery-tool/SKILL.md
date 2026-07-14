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
- ../../knowledge/production/story-to-game.md
- ../../knowledge/production/shanyin-director-methodology.md
- ../../knowledge/production/shanyin-director-styles.md
---

# 宣发交付工具 v5.0

## 职责

这是可选工具，不进入默认创作完成率。仅在剧本需要投放、交付、视觉包装或互动改编时调用。

## 执行流程

1. **先跑交付门禁**（`modules/delivery-check.md`）：质量 ≥B 级 + 合规通过 + 集数/字数完整，任一不过只输出缺口清单
2. 生成视觉物料（`modules/visual-anchor.md`）与营销文案（`modules/marketing-copy.md`）
3. 按需生成互动改编版本（`modules/story-to-game.md`）
4. 组装 production_package 并附核验表

## 标准输出要求

- 剧名备选
- 海报 / 封面视觉提示词
- 主角视觉锚点
- 平台标题
- 简介
- 投流短文案
- 高光切片建议
- 交付完整性检查
- 互动改编可能性

## 触发方式

```
@drama-delivery-tool 生成宣发交付包
```

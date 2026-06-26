---
name: drama-delivery-tool
version: 4.0.0
description: 宣发交付工具：吸收制作发行能力，输出 production_package。
tags:
- 宣发
- 交付
- 视觉提示词
- 投流文案
- 互动改编
dept: 宣发交付部
modules:
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
- ../../modules/visual-anchor.md
- ../../modules/marketing-copy.md
- ../../modules/delivery-check.md
- ../../modules/story-to-game.md
---

# 宣发交付工具 v4.0

## 职责

这是可选工具，不进入默认创作完成率。仅在剧本需要投放、交付、视觉包装或互动改编时调用。

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

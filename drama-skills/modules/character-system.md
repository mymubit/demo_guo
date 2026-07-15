# 模块：人物系统设计

## 目标
建立能驱动冲突、关系变化和全剧弧光的人物系统。

## 输入
- 核心概念、目标受众、主冲突
- 已确认的题材与世界规则

## 引用规则
- `t1.global.character_rules.age-logic`
- `t1.global.character_rules.density-arc`
- `t1.global.character_rules.relationship-dynamics`
- `t1.global.character_rules.voice-anchor`

## 输出
- `characters[]`
- `relationship_map[]`

## 执行步骤
1. 为核心人物定义 Want、Need、Ghost、Lie、Flaw。
2. 用年龄、处境和前史验证其决策逻辑。
3. 建立双方诉求和权力来源都明确的关系边。
4. 为每人定义弧光四点、`voice_tag` 与 `visual_anchor`。
5. 合并只传递信息、没有独立欲望的配角。

## 失败条件
- 角色行为只服务情节，没有稳定欲望。
- 关系变化没有可见触发事件。

## 自检清单
- [ ] 每个核心角色可用一句话说明欲望与恐惧
- [ ] 遮名后主要人物台词仍可区分
- [ ] 弧光转折由事件触发而非性格突变

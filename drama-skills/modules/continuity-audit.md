# 模块：连续性终审

## 目标
独立检查跨集人物、知识、关系、道具、世界规则和伏笔状态是否一致。

## 输入
- `latest_script`
- `story_bible`
- `narrative_plan`
- 各集 `memory_checkpoint`

## 引用规则
- `t1.global.continuity.checkpoint`
- `t1.global.world_rules.consistency`
- `t1.global.foreshadowing_rules.payoff`

## 输出
- 写入 `quality_report.defects` 的连续性问题
- 每个问题的集数、证据、冲突事实与修复建议

## 执行步骤
1. 按集重放人物物理、情感、认知和目标状态。
2. 检查关系、道具、世界规则和角色知识边界。
3. 核对伏笔状态、计划回扣集和逾期项。
4. 区分正文错误、检查点错误和上游蓝图冲突。

## 失败条件
- 只给“前后不一致”结论，没有双向证据。
- 评分裁判直接改写剧本。

## 自检清单
- [ ] 每个问题至少引用两个冲突位置
- [ ] 明确责任层级和建议修复位置
- [ ] 未把有铺垫的角色变化误判为性格突变

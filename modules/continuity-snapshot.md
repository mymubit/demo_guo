# 模块：连续性快照

## 目标
在分批逐集生成时保存最小而充分的事实状态，防止人物、伏笔、关系和道具前后矛盾。

## 输入
- 当前集正文
- 上一版 `memory_checkpoint`
- 本集分集卡

## 引用规则
- `t1.global.continuity.checkpoint`
- `t1.global.learned_rules.lr008`
- `foundation/constraints/continuity-checkpoint.yaml`

## 输出
- `memory_checkpoint`

## 执行步骤
1. 更新人物物理、情感、认知和目标状态。
2. 更新线索、伏笔、关系和关键道具状态。
3. 记录本集节奏结果及未兑现承诺。
4. 写出下一集必须承接和不得冲突的约束。

## 失败条件
- 只复述本集剧情，没有状态变化。
- 删除仍未解决的线索或伏笔。

## 自检清单
- [ ] Schema 必填字段完整
- [ ] 所有未回扣伏笔都有状态和计划位置
- [ ] 下一集约束可直接用于生成前检查

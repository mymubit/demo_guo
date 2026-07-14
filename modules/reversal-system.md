# 模块：反转体系（兼容入口）

> 当前角色挂载兼容入口；完整执行流程已合并到 `modules/reversal-foreshadowing.md`。

## 输入

- 全剧结构或分集卡
- 当前伏笔状态
- 题材 `reversal_density`

## 引用规则

- `t1.global.foreshadowing_rules.density`
- `t1.global.foreshadowing_rules.payoff`
- `t1.global.foreshadowing_rules.types`
- `foundation/constraints/commercial-formulas.yaml#metrics.s_reversal_window`

## 执行

调用 `modules/reversal-foreshadowing.md` 完成揭露、线索、埋点与回扣闭环。

## 失败条件

- 只有反转点，没有可追踪伏笔。
- 在模块内重新定义窗口、密度或铺垫数值。

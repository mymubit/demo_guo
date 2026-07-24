# 模块：反转与伏笔闭环

## 目标
用逆向设计建立“揭露—线索—埋点—回扣”的可追踪闭环。

## 输入
- 全剧结构或分集卡
- 当前伏笔清单
- 题材 `reversal_density`

## 引用规则
- `t1.global.foreshadowing_rules.density`
- `t1.global.foreshadowing_rules.payoff`
- `t1.global.foreshadowing_rules.types`
- `foundation/constraints/narrative-metrics.yaml#s_reversal_foreshadow`

灵感库（可选参考）：`inspirations/inspirations.md`（反转创意）。

## 输出
- `major_reversal_positions[]`（唯一写入者，见 `contracts/artifacts.yaml#field_writers`）
- `foreshadowing_table[]`（唯一写入者）
- 分集 `foreshadowing.setup/payoff`

story-bible 阶段写全剧反转位与伏笔表；episode-designer 阶段只读全剧表、写分集埋点/回扣，禁止改全局反转位。

## 执行步骤
1. 先确定揭露改变了什么认知与格局。
2. 倒推观众回看时能够识别的公平线索。
3. 为每条线索记录埋点集、状态和计划回扣集。
4. 回扣时同时兑现情节信息与情感价值。

## 失败条件
- 揭露前不存在可验证线索。
- 反转后不改变后续行动或关系。

## 自检清单
- [ ] 每个反转均可追溯到具体埋点
- [ ] 已逾期伏笔进入 continuity checkpoint
- [ ] S级揭露位于约束窗口且有仪式化场景

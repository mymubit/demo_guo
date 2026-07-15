# 模块：全剧结构设计

## 目标
把核心冲突分配到可缩放的六阶段结构，并建立主线、转折、付费点和伏笔骨架。

## 输入
- 核心概念、人物系统、世界规则
- `episode_count`
- `project_brief.rule_params`

## 引用规则
- `t1.global.series_structure.six-stage`
- `t1.global.series_structure.boundary`
- `t1.global.conflict_escalation.upgrade-protocol`
- `t1.global.foreshadowing_rules.density`
- `foundation/constraints/series-scale.yaml`

## 输出
- `series_structure.main_storyline`
- `series_structure.six_stage_structure`
- `conflict_escalation_chain`
- `major_reversal_positions`
- `paywall_distribution`
- `foreshadowing_table`

## 执行步骤
1. 按题材参数或基础占比分配六阶段集数。
2. 为每阶段定义目标、冲突升级和不可逆转折。
3. 布置付费承诺、反转揭露和伏笔回扣窗口。
4. 校验所有阶段集数之和等于总集数。

## 失败条件
- 阶段只有剧情摘要，没有功能和转折。
- 在全剧结构层提前写逐集场景。

## 自检清单
- [ ] 六阶段集数完整且无重叠
- [ ] 冲突至少在范围、烈度、信息或后果上升级
- [ ] 所有关键揭露都有前置伏笔

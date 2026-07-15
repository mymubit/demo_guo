# 模块：付费卡点设计

## 目标
设计建立投入、制造承诺并及时兑现的付费节点，而不是机械断章。

## 输入
- 全剧结构与分集卡
- 目标商业模式
- 当前人物关系和悬念状态

## 引用规则
- `t1.global.payment_checkpoint_3card.types`
- `t1.global.payment_checkpoint_3card.timing`
- `t1.global.learned_rules.lr003`
- `foundation/constraints/commercial-formulas.yaml`

## 输出
- `paywall_distribution[]`
- 分集 `paywall_hook`
- 承诺与兑现集映射

## 执行步骤
1. 选择情感卡、悬念卡或爽感卡。
2. 在卡点前完成必要的情感或信息投入。
3. 把承诺写成下一阶段必须回答的具体问题。
4. 在约束期限内兑现，再建立下一层承诺。

## 失败条件
- 卡点前没有建立投入。
- 付费后回避或拖延原承诺。

## 自检清单
- [ ] 首卡与习惯卡未混淆
- [ ] 卡点前钩子达到要求等级
- [ ] 每个付费承诺都有兑现位置

# 模块：全剧情绪曲线

## 目标
为全剧建立随结构推进、付费承诺和角色弧光变化的逐集情绪目标。

## 输入
- 六阶段结构
- 题材 `emotion_curve`
- 主要角色弧光与付费节点

## 引用规则
- `t1.global.qdn_emotion_model.summary`
- `t1.global.series_structure.six-stage`
- `foundation/constraints/series-scale.yaml#emotion_terms`

## 输出
- `series_structure.series_emotion_curve`
- 全剧 ET、主要 TP 与喘息集位置

## 执行步骤
1. 将题材八节点曲线映射到实际集数。
2. 标注全剧谷底、关键转折和最终兑现。
3. 检查付费卡点前是否处于有效上升沿。
4. 安排必要喘息，但避免连续低推进。

## 失败条件
- 曲线只持续上升，没有谷底和恢复。
- 情绪峰值与结构事件、角色选择无对应关系。

## 自检清单
- [ ] 每个主要 TP 都对应具体事件
- [ ] 喘息集不连续
- [ ] 结局情绪是前序选择的兑现

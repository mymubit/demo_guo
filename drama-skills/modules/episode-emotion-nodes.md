# 模块：单集情绪节点

## 目标
将全剧情绪目标细化为单集八节点、EV/ET/TP 和双轨节奏。

## 输入
- 本集分集卡
- 全剧情绪曲线
- 上一集 `rhythm_state`

## 引用规则
- `t1.global.qdn_emotion_model.summary`
- `t1.global.episode_emotion_8nodes.summary`
- `foundation/constraints/series-scale.yaml#emotion_terms`

## 输出
- `emotion_nodes`
- `rhythm_tag`
- 八节点目标值

## 执行步骤
1. 根据本集核心事件确定起点、ET、TP、EV和余波。
2. 补齐八个时间节点并说明触发事件。
3. 标记情节节奏与情感节奏。
4. 与相邻两集比较，避免情绪平台和节奏同格。

## 失败条件
- 节点只有数值，没有触发事件。
- 峰值与本集核心选择无关。

## 自检清单
- [ ] 八节点覆盖完整
- [ ] EV/ET/TP 均有事件依据
- [ ] 相邻集节奏存在可感知变化

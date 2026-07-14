# 模块：情绪蓝图（兼容入口）

> 当前角色挂载兼容入口；底层能力已拆为两个单一职责模块。

## 路由

- 全剧层：执行 `modules/series-emotion-curve.md`
- 单集层：执行 `modules/episode-emotion-nodes.md`

## 输入

- `scope=series|episode`
- 对应层级的结构、题材情绪曲线与相邻状态

## 引用规则

- `t1.global.qdn_emotion_model.summary`
- `t1.global.episode_emotion_8nodes.summary`
- `foundation/constraints/series-scale.yaml#emotion_terms`

## 输出

- `scope=series`：`series_structure.series_emotion_curve`
- `scope=episode`：`emotion_nodes`、`rhythm_tag`

## 失败条件

- 未声明层级却同时生成全剧曲线和单集节点。
- 复制固定曲线而未结合题材参数与具体事件。

# 模块：制片可拍性标记

## 目标
在正文生成时识别资源复杂度和不可拍内容，为后续预算与交付提供结构化依据。

## 输入
- 当前集场景与动作
- `foundation/constraints/production-feasibility.yaml`

## 引用规则
- `t1.global.production_feasibility.tagging`
- `t1.global.production_feasibility.alternative`
- `t1.global.production_feasibility.camera-visible`

## 输出
- 每集 `production_notes.tags`
- `complexity_score` 与 `complexity_band`
- 高成本场景及低成本替代方案

## 执行步骤
1. 逐场标记场地、时间、人数、动作、道具、特效和特殊主体。
2. 按配置权重计算本集复杂度。
3. 对高复杂度场景提供保持戏剧功能的替代方案。
4. 把无法由镜头、声音或表演呈现的内容退回场景重写。

## 失败条件
- 输出未经来源支持的精确拍摄金额。
- 为降成本直接删除核心转折或人物选择。

## 自检清单
- [ ] 所有高复杂度场景均有标签
- [ ] 替代方案保留原场景戏剧功能
- [ ] 复杂度结果可供预算模块直接消费

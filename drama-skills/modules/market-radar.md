# 模块：市场雷达

> 挂载角色：`drama.topic-director`（立项市场判断）

## 目标

在选题定调阶段完成市场判断，输出进入 `project_brief` 的 `market_opportunity`、`competitor_references`、`differentiation_strategy` 字段。

## 输入与约束

- 核心概念、目标受众与 `target_platform`
- `foundation/constraints/commercial-formulas.yaml`
- `foundation/constraints/platform-profiles.yaml`

## 执行步骤

1. **热点定位**：结合 `knowledge/market/douyin-formulas.md`（标签三级体系）与 `knowledge/market/market-insights.md`（平台基准），判断本选题所属标签组合的热度层级（通用型/场景型/情绪型）
2. **竞品扫描**：列出同题材 2-3 部头部竞品，各提炼 1 条可借鉴点（inspiration）+ 1 条避雷点（avoidance）
3. **空白点识别**：从「同标签组合下未被满足的情绪/身份/世界观变体」中找差异化切口（可用四轴矩阵换轴法：保留主情绪，替换身份或世界观轴）
4. **梦境三指标预估**：按 `commercial-formulas.yaml` 的定义、目标线和熔断线打分
5. **平台适配**：只有在平台规则来源和验证时间有效时给出专项结论，否则标记待核验

## 输出要求

- 市场机会判断：1 段话，含热度层级 + 空白点
- 竞品参考：≥2 条，每条含借鉴 + 避雷
- 差异化策略：与头部竞品至少 1 个明确差异点（不能是「我们质量更好」）

## 自检清单

- [ ] 差异化策略具体到情节/人设/世界观层面，可被下游执行
- [ ] 竞品避雷点能转化为创作禁止项
- [ ] 数据引用注明来源（市场数据具有时效性，冲突时以后台配置的最新数据为准）

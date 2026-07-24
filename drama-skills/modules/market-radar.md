# 模块：市场雷达

> 挂载角色：`drama.topic-director`（立项市场判断）

## 目标

在选题定调阶段完成市场判断，输出进入 `project_brief` 的 `market_opportunity`、`competitor_references`、`differentiation_strategy` 字段。

## 输入

- 核心概念、目标受众与 `target_platform`

## 引用规则

- `foundation/constraints/commercial-formulas.yaml#metrics.tag_mix`
- `foundation/presets/platform-profiles.yaml`
- `knowledge/market/douyin-formulas/catalog.yaml`（按题材匹配；命中后注入对应公式文件）
- 公式包文件：`knowledge/market/douyin-formulas/_shared.md`、`knowledge/market/douyin-formulas/hidden-identity-reversal.md`、`knowledge/market/douyin-formulas/dual-power-game.md`、`knowledge/market/douyin-formulas/fate-reversal-awakening.md`、`knowledge/market/douyin-formulas/sweet-daily.md`、`knowledge/market/douyin-formulas/era-empathy.md`、`knowledge/market/douyin-formulas/ancient-aesthetic.md`、`knowledge/market/douyin-formulas/suspense-emotion.md`、`knowledge/market/douyin-formulas/anti-trope.md`
- `knowledge/market/industry-benchmarks.md`（长文参考）

梦境三指标由 `formula-analysis` 独占评估，本模块不重复打分。

## 执行步骤

1. **热点定位**：结合 `knowledge/market/douyin-formulas/catalog.yaml`（题材匹配目录与公式包）、`knowledge/market/industry-benchmarks.md`（平台基准）与 `knowledge/market/market-insights.md`（动态摄入），判断本选题所属标签组合的热度层级（通用型/场景型/情绪型）
2. **竞品扫描**：列出同题材 2-3 部头部竞品，各提炼 1 条可借鉴点（inspiration）+ 1 条避雷点（avoidance）
3. **空白点识别**：从「同标签组合下未被满足的情绪/身份/世界观变体」中找差异化切口（可用四轴矩阵换轴法：保留主情绪，替换身份或世界观轴）
4. **平台适配**：只有在平台规则来源和验证时间有效时给出专项结论，否则标记待核验

## 输出

- `project_brief.market_opportunity`：1 段话，含热度层级 + 空白点
- `project_brief.competitor_references[]`：≥2 条，每条含借鉴 + 避雷
- `project_brief.differentiation_strategy`：与头部竞品至少 1 个明确差异点（不能是「我们质量更好」）

## 失败条件

- 竞品结论无具体作品与集数级证据。
- 差异化停留在口号层，无法转成创作指令。

## 自检清单

- [ ] 差异化策略具体到情节/人设/世界观层面，可被下游执行
- [ ] 竞品避雷点能转化为创作禁止项
- [ ] 数据引用注明来源（市场数据具有时效性，冲突时以后台配置的最新数据为准）

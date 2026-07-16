# 模块：爆款公式分析

> 挂载角色：`drama.topic-director`（立项爆款因子核验）
> 梦境三指标由本模块**独占**评估；market-radar 只做热点/竞品/差异化，不重复评。

## 目标

用商业量化公式核验选题的爆款潜力，产出可执行的爆款因子与补强方案。

## 输入

- 核心概念、目标受众与题材参数
- 已知的商业模式与集数

## 引用规则

- `foundation/constraints/commercial-formulas.yaml`
- `foundation/constraints/series-scale.yaml`

本模块只负责应用公式，不维护任何数值。

## 输出

- `project_brief.blockbuster_factors[]`
- `project_brief.first_episode_hook`、`project_brief.paywall_direction`
- 梦境三指标预估（safety / satisfaction / realism，按约束目标带与熔断线）

## 执行步骤

1. 读取商业公式中的五类指标并逐项预估
2. 任一指标低于标准 → 在 `project_brief.blockbuster_factors` 中标注补强方案
3. 用「人格共鸣」检验：除了爽感，观众能否说出「这个角色像我」（2026 转型趋势，见 `knowledge/market/douyin-formulas.md`）

## 失败条件

- 只给结论不给预估依据。
- 指标不达标却未提供补强方案。

## 自检清单

- [ ] 五项量化指标全部预估并写入简报
- [ ] 爆款因子 ≥3 条且各自对应具体情节设计方向
- [ ] 梦境三指标均按约束中的目标线与熔断线判断

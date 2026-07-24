# 模块：制作预算分级

## 目标
根据终稿的制片复杂度输出可审计的资源预算带，不伪造精确报价。

## 输入
- `latest_script.production_notes`
- 高成本场景与替代方案
- 可选地区、币种和价格版本

## 引用规则
- `t1.global.budget_estimation.band-only`
- `foundation/presets/production-feasibility.yaml`

## 输出
- `production_package.production_plan.complexity_band`
- 主要成本驱动项
- 推荐替代方案
- 条件充分时的金额区间与未计入项

## 执行步骤
1. 汇总全剧复杂度标签和高成本场景。
2. 按配置计算资源复杂度与预算带。
3. 比较原方案和低成本替代方案。
4. 仅在价格上下文完整时输出金额区间。

## 失败条件
- 缺少地区或价格版本却给出精确金额。
- 忽略安全、合规和核心剧情要求压低预算。

## 自检清单
- [ ] 每个成本驱动项可追溯到具体场景
- [ ] 金额估算包含币种、地区、版本和排除项
- [ ] 默认只输出复杂度与预算带

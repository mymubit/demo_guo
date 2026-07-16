# 模块：交付验证

> 挂载角色：`drama.delivery-tool`（production_package 的前置门禁）

## 目标

作为交付前的总闸，逐项核验质量、合规、完整性与制片可行性，阻断不可交付的项目。

## 输入

- `quality_report` + `compliance_report`（缺任一 → 直接不可交付）
- `latest_script`、`story_bible`（集数完整性对照）
- 项目 `scoring_preset` 与 `target_platform`

## 引用规则

- `t3.drama-delivery-tool.delivery.gate`
- `foundation/constraints/scoring-presets.yaml`
- `foundation/constraints/quality-scoring.yaml`
- `foundation/constraints/script-format.yaml`
- `foundation/constraints/platform-profiles.yaml`

## 门禁规则（任一不过 → 只输出「不可交付 + 缺口清单」）

| 检查项 | 标准 | 依据 |
|--------|------|------|
| 合规结论 | compliance_report.overall_result = 通过 | P0/P1 熔断（compliance-core.yaml） |
| 质量等级 | 达到当前评分预设通过线，且 `delivery_eligible=true` | `quality-scoring.yaml` + `scoring-presets.yaml` |
| 集数完整 | 实际集数 = story_bible 规划集数，无缺集断号 | — |
| 字数达标率 | ≥95% 的集落入 script-format 区间 | script-format.yaml |
| 付费墙钩子 | 付费卡点前一集集末钩子为全剧最强之一 | LR-003 |
| 版本正确 | 打包对象为 `latest_script` | 产物解析规则 |
| 制片可行性 | 已输出复杂度、预算带和高成本替代方案 | production-feasibility.yaml |
| 平台政策 | 请求 `release` 时，政策版本已验证且上架阻断项为 0 | platform-profiles.yaml |

## 输出

- `production_package.production_plan`（含核验表：项 × 结果 × 证据）
- `production_package.release_checklist`
- 不可交付时：缺口清单（含责任角色），不产出其余物料

## 执行步骤

1. 读取 quality_report + compliance_report（缺任一报告 → 直接不可交付，提示先跑质检环）
2. 按上表逐项核验，输出核验表（项 × 结果 × 证据）
3. 全部通过 → 组装 production_package（制作计划 + 上架清单 + 分镜/视觉/营销物料 + 核验表）
4. 任一不过 → 输出缺口清单，标注责任角色（修复官/合规官/正文官）

## 失败条件

- 缺报告仍出具交付结论。
- 门禁未全过却产出宣发物料。

## 自检清单

- [ ] 八项门禁全部有明确结论与证据
- [ ] 交付包内容与核验通过的版本一致
- [ ] 缺口清单可直接转为对应角色的执行指令

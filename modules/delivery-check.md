# 模块：交付验证

> 挂载角色：`drama.delivery-tool`（production_package 的前置门禁）

## 门禁规则（任一不过 → 只输出「不可交付 + 缺口清单」）

| 检查项 | 标准 | 依据 |
|--------|------|------|
| 合规结论 | compliance_report.overall_result = 通过 | P0/P1 熔断（compliance-core.yaml） |
| 质量等级 | 达到当前评分预设通过线 | `quality-scoring.yaml` + `scoring-presets.yaml` |
| 集数完整 | 实际集数 = story_bible 规划集数，无缺集断号 | — |
| 字数达标率 | ≥95% 的集落入 script-format 区间 | script-format.yaml |
| 付费墙钩子 | 付费卡点前一集集末钩子为全剧最强之一 | LR-003 |
| 版本正确 | 打包对象为最新版本（polished_script 优先） | 质检环规则 |

## 执行步骤

1. 读取 quality_report + compliance_report（缺任一报告 → 直接不可交付，提示先跑质检环）
2. 按上表逐项核验，输出核验表（项 × 结果 × 证据）
3. 全部通过 → 组装 production_package（剧本终稿 + 视觉物料 + 营销文案 + 核验表）
4. 任一不过 → 输出缺口清单，标注责任角色（修复官/合规官/正文官）

## 自检清单

- [ ] 六项门禁全部有明确结论与证据
- [ ] 交付包内容与核验通过的版本一致
- [ ] 缺口清单可直接转为对应角色的执行指令

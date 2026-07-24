# 模块：平台上架清单

## 目标
把平台政策、备案、AI标识、版权和交付材料转化为可执行的上架检查表。

## 输入
- `target_platform`
- 平台政策版本与验证时间
- `quality_report`、`compliance_report`、`production_package`

## 引用规则
- `t1.global.platform_ops.release-check`
- `t4.global.platform_specific.declared-target`
- `t4.global.three_phase_checklist.gates`
- `foundation/presets/platform-profiles.yaml`

## 输出
- `production_package.release_checklist`
- 阻断项、待补材料、政策来源和验证时间

## 执行步骤
1. 确认目标平台及有效政策版本。
2. 检查质量、合规、原创性、AI标识和版权授权。
3. 核对剧本、蓝图、分集、报告和宣发材料完整性。
4. 对未知或过期政策标记阻断并要求人工复核。

## 失败条件
- 平台政策未验证却输出“可直接发布”。
- 用通用规则冒充平台专项规则。

## 自检清单
- [ ] 每项结论有政策来源和版本
- [ ] 阻断项与建议项明确区分
- [ ] 缺失材料有责任人和下一步

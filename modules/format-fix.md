# 模块：格式修复

> 挂载角色：`drama.revision-master`（修复阶段格式治理）
> 格式数值 SSOT：`foundation/constraints/script-format.yaml`

## 目标

把剧本文本修复到 100% 符合商业格式三件套，FER 降到目标线以下。

## 输入

- `latest_script` 指定 `episode_range` 的全文
- 评分报告 format 维度扣分项

## 引用规则

- `t1.global.writing_prohibitions.format-ssot`
- `t1.global.writing_prohibitions.unfilmable`
- `foundation/constraints/script-format.yaml`
- `foundation/constraints/quality-scoring.yaml#format_error_rate`

## 标准格式三件套

```
场景头：集号-场景号 时间（日/夜/晨/昏） 内/外 地点
台词：  角色（情绪）：台词内容
动作：  △【景别】动作描述（15-25字）
```

## 违规项与修复

| 违规 | 修复 |
|------|------|
| 台词用引号 `"..."` | 改「角色（情绪）：」冒号格式 |
| 心理描写（"她心想…"） | 删除或转为动作/表情外化 |
| 方括号场景头 `[客厅]` | 改标准场景头格式 |
| 独立【画面】行 | 并入 △ 动作行并标注景别 |
| "她感到…" 类叙述 | 转为可拍摄的外部动作 |

## FER（格式错误率）

FER = 格式错误行数 / 总行数。目标线、警告线与熔断线读取
`foundation/constraints/quality-scoring.yaml#format_error_rate`。

## 输出

- `polished_script.episodes[].script`（格式修复后全文）
- `polished_script.revision_summary` 中的 FER 修复前后对比与违规统计

## 执行步骤

1. 全文扫描五类违规项，逐条修复并计数
2. 复算 FER，输出修复前后对比
3. 校验场景头连续性（集号-场景号递增无跳漏）
4. 输出格式自检结果（违规类型 × 数量 × 修复状态）

## 失败条件

- 修复后 FER 仍高于警告线。
- 修复改动了台词语义或剧情事实。

## 自检清单

- [ ] 修复后 FER 达到 `quality-scoring.yaml#format_error_rate.target_max`
- [ ] 场景头/台词/动作三件套 100% 符合模式
- [ ] 无残留心理描写与叙述性语句

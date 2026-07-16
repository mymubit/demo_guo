# 模块：字数治理

> 挂载角色：`drama.revision-master`（修复阶段字数与台词占比治理）
> 数值 SSOT：`foundation/constraints/script-format.yaml`；本模块不重复维护区间。

## 目标

在不损伤情绪曲线与钩子的前提下，把每集字数与台词占比治理进 SSOT 区间。

## 输入

- `latest_script` 指定 `episode_range` 的全文
- 评分报告 format 维度中的字数/占比扣分项

## 引用规则

- `foundation/constraints/script-format.yaml`
- `t1.global.writing_requirements.commercial-format`

## 输出

- `polished_script.episodes[].script`（治理后全文）
- `polished_script.revision_summary` 中的逐集统计表（修复前 → 修复后）

## 治理策略

| 症状 | 优先处理顺序 |
|------|------------|
| 字数不足 | ① 延伸情绪高点场景（加拉锯回合）→ ② 补集末钩子铺垫 → ③ 增加对峙层次。禁止注水过渡场景 |
| 字数超标 | ① 删纯过渡场景 → ② 合并功能重复的对话 → ③ 压缩动作描述至 15-25 字。禁止削情绪高点 |
| 台词占比不足 | 叙述性动作改对话呈现（信息借人物之口）；内心活动转为向他人倾诉/自言自语 |
| 台词占比过高 | 连续长对话中插入动作反应；部分交代性台词转 △ 动作 |

## 执行步骤

1. 逐集统计：字数、台词字符占比、场景数，对照 SSOT 区间
2. 越界集按上表策略修复，修复时保持情绪曲线与钩子不受损
3. 输出逐集统计表（修复前 → 修复后）

## 失败条件

- 用注水场景凑字数。
- 治理后 EV 峰值或集末钩子被削弱。

## 自检清单

- [ ] 全部集数落入 SSOT 字数区间，并按交付门禁计算达标率
- [ ] 台词占比落入 `script-format.yaml#dialogue_ratio` 区间
- [ ] 修复未削弱 EV 峰值与集末钩子
- [ ] 每集场景数仍在 1-3 内

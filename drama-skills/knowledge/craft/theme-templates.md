# 题材矩阵与参数合成（指针页）

> **本文件不维护任何数值与枚举**。历史版本曾在此复述预设表与情绪底稿，
> 与 SSOT 漂移后已清理；一切以下述文件为准。

## SSOT

| 内容 | SSOT |
|------|------|
| 受众频道 / 四轴 / 主角结构 / 风味标签枚举 | `foundation/theme-matrix.yaml` |
| 参数合成（emotion 底稿 + 各维 delta + 合并规则） | `foundation/theme-matrix.yaml#param_synthesis` |
| 组合约束（互斥 / 世界观依赖） | `foundation/theme-matrix.yaml#tag_constraints` |
| 预设卡片 | `foundation/theme-matrix.yaml#preset_templates` |
| 创新组合种子 | `foundation/theme-matrix.yaml#featured_combos` |
| 自由创意推断词表 | `foundation/theme-matrix.yaml#topic_inference` |

## 三条解析路径

| 路径 | 触发 | theme_code | 参数来源 |
|------|------|------------|----------|
| 矩阵主路径 | 用户选频道+四轴（+结构+标签） | `matrix` | `param_synthesis` 合成 `rule_params` |
| 预设卡片 | 用户直接点卡片 | `matrix` + `preset_theme_code` | 预设 dims 走同一套 synthesis |
| 自由创意 | 仅 `core_idea` | `matrix` | topic-director 按 `topic_inference` 推断后合成 |

预设卡片**不是**独立 archetype：点卡片后仍生成 `theme_code=matrix` + `rule_params`，
`preset_theme_code` 仅作 UI 标签。

## 校验

```bash
python tools/validators/validate_theme_matrix.py   # 枚举/delta/约束/幂等
python tools/optimizers/synthesize_matrix_params.py  # 合成示例
```

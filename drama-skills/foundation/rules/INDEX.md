# 规则主题索引（INDEX）

> 用途：按**创作查找路径**定位规则文件，减少在 17 个 YAML 间猜测。  
> 数值约束仍可能在 `foundation/constraints/`；本索引标注「规则叙述」主文件。  
> 合并规则簇（总纲阶段 C）后请同步更新本页。

## 按创作主题

| 主题 | 主要文件 | 常见相关 constraints |
|------|----------|----------------------|
| 理念 / 哲学 | `philosophy.yaml` | — |
| 概念与选题入口 | `concept-rules.yaml` | `commercial-formulas.yaml` |
| 人物（C3 簇） | `02-character.yaml` | — |
| 结构 / 节奏（C3 簇） | `03-structure.yaml`、`stage-playbook.yaml` | `series-scale.yaml`、`narrative-metrics.yaml` |
| 叙事工艺 | `narrative-craft.yaml` | `narrative-metrics.yaml` |
| 钩子 / 付费（C2 簇） | `05-hooks-payoff.yaml` | `narrative-metrics.yaml`、`commercial-formulas.yaml` |
| 情节 / 反转 | `plotting-rules.yaml` | `narrative-metrics.yaml` |
| 场景与对白（C3 簇） | `04-scene-dialogue.yaml` | `script-format.yaml` |
| 世界观 | `world-rules.yaml` | — |
| 题材矩阵 | `genres/matrix.yaml` | `theme-matrix.yaml`（若在 constraints/presets） |
| 评分 / 质量 | `scoring-core.yaml` | `quality-scoring.yaml`、`scoring-presets.yaml` |
| 合规 | `compliance-core.yaml` | — |
| 原创性 | `originality-rules.yaml` | — |
| 制片交付 | `production-rules.yaml` | `platform-profiles.yaml` |
| 习得规则 | `learned-rules.yaml` | — |

## 钩子 / 付费（C2 已聚合）

查找「钩子密度 / 首集钩子 / 付费卡点」：

1. **`05-hooks-payoff.yaml`** — `hook_effectiveness` + `payment_checkpoint_3card`（叙述）  
2. `foundation/constraints/commercial-formulas.yaml` — 首集钩子数量、付费兑现（数值 SSOT）  
3. `foundation/constraints/narrative-metrics.yaml` — 开场分层窗口、S 级反转铺垫（数值 SSOT）  
4. **`03-structure.yaml#rhythm_rules`** — 双轨节奏与钩子密度基线（题材覆盖仍见 genres/matrix）

## 结构与节奏（C3 已聚合）

查找「六阶段 / 分集卡 / 连续性 / 双轨节奏」：

1. **`03-structure.yaml`** — series_structure / episode_card / continuity / rhythm_rules  
2. `foundation/constraints/series-scale.yaml` — 阶段占比与集数（数值 SSOT）  
3. `stage-playbook.yaml` — 按角色的阶段 playbook（tier3，未并入）

## 场景与对白（C3 已聚合）

查找「台词 / AI 腔 / 场景单元 / 写作禁令」：

1. **`04-scene-dialogue.yaml`** — dialogue_* / writing_* / ai_tone_forbidden  
2. `foundation/constraints/script-format.yaml` — 字数与格式禁止项（数值 SSOT）

## 文件清单（物理）

- `philosophy.yaml`
- `concept-rules.yaml`
- `02-character.yaml`
- `03-structure.yaml`
- `05-hooks-payoff.yaml`
- `04-scene-dialogue.yaml`
- `narrative-craft.yaml`
- `plotting-rules.yaml`
- `world-rules.yaml`
- `stage-playbook.yaml`
- `scoring-core.yaml`
- `compliance-core.yaml`
- `originality-rules.yaml`
- `production-rules.yaml`
- `learned-rules.yaml`
- `genres/matrix.yaml`

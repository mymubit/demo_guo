# 评分预设（Scoring Presets）

> **参考说明**；等级、维度与权重 SSOT：`foundation/constraints/quality-scoring.yaml`。
> 预设 SSOT：`foundation/constraints/scoring-presets.yaml`。
> 
> **使用方式**：drama.script-scorer 执行评分时，根据使用场景选择对应预设。
> 默认使用 `standard` 预设；`standard` 的通过线即质检环的 B 级线（75）。
> `strict` / `relaxed` 属于对默认阈值的显式覆盖，仅在用户指定时生效。

---

## 四个评分预设

| 预设ID | 名称 | 适用场景 |
|--------|------|---------|
| `standard` | 标准（推荐） | 日常创作默认评分 |
| `strict` | 严格 | 精品筛选，增强叙事、逻辑和人物要求 |
| `relaxed` | 宽松 | 内测或初稿，不用于正式发布结论 |
| `rhythm_first` | 节奏优先 | 强钩子、强留存题材 |

---

## 执行约束

所有预设都必须使用同一十维：

`format / narrative / conflict / character / emotion / logic / satisfaction / hooks / paywall / genre_fit`

具体通过线与十维权重只读取 `foundation/constraints/scoring-presets.yaml`，不得重新聚合成“格式/节奏/内容/制作”四维。

---

## 平台推荐预设

| 目标平台 | 推荐预设 | 原因 |
|---------|---------|------|
| 抖音 | `rhythm_first` | 平台算法高度依赖钩子和留存 |
| 快手 | `standard` | 情感共鸣比节奏更重要 |
| 微信小程序 | `strict` | 付费用户对质量要求更高 |
| 精品化创作 | `strict` | 追求S级标准 |
| 快速原型验证 | `relaxed` | 先完成再提升 |

---

## 关键阈值

```
等级阈值：foundation/constraints/quality-scoring.yaml
预设通过线：foundation/constraints/scoring-presets.yaml
单维返工线：quality-scoring.revision_threshold
```

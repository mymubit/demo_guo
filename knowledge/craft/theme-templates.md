# 规则模板与四轴合成（Rule Params）

> **重要：8 个 archetype 模板 ≠ 四轴的全部答案**
>
> | 路径 | 触发 | theme_code | 参数来源 |
> |------|------|------------|----------|
> | **四轴矩阵（主路径）** | 用户选 emotion/identity/conflict/world | `matrix` | `param_synthesis` 合成 `rule_params` |
> | **预设卡片（快捷）** | 用户直接点「家庭复仇」等卡片 | `matrix` + `preset_theme_code` | 用预设对应的四轴走同一套 synthesis |

四轴选题**不再**映射到 8 个 archetype；以前 weighted_score 会导致「复仇+重生+家族+古代」被错误判成 `time-travel` 或 `family-revenge`。

---

## 四轴 + 风味标签 → rule_params（v1.3 全量）

SSOT：`foundation/theme-matrix.yaml`

| 层 | 规模 | 说明 |
|----|------|------|
| 四轴 | 9×9×9×9 = **6561** 个骨架 | 情感/身份/冲突/世界 |
| 风味标签 | **69 项**，最多 **5** 个 | 12 大类 |
| 创新组合 | **32** 条 featured | 可直接点选或作进化种子 |

```
四轴 + tags → synthesize → rule_params（theme_code=matrix）
```

枚举与分类见 `theme-matrix.yaml`；校验：

```bash
python build/validate_theme_matrix.py
python build/synthesize_matrix_params.py
```

---

## 8 个预设卡片（快捷四轴填充）

仅当用户**不手动选轴**、直接点卡片时使用。每张卡片等价于一组固定 `genre_matrix`：

| preset_theme_code | 中文 | 等价四轴 |
|-------------------|------|----------|
| `family-revenge` | 家庭伦理复仇 | 复仇 / 弱势 / 家族 / 都市 |
| `domineering-ceo` | 豪门霸总 | 爱情 / 隐藏大佬 / 情感 / 都市 |
| `sweet-pet` | 甜宠虐恋 | 爱情 / 普通人 / 情感 / 都市 |
| `time-travel` | 穿越重生 | 复仇 / 重生 / 家族 / 都市 |
| `urban-counterattack` | 都市逆袭 | 野心 / 弱势 / 职场 / 都市 |
| `ancient-power` | 古装权谋 | 野心 / 隐藏大佬 / 权谋 / 古代 |
| `mystery-reversal` | 悬疑反转 | 悬疑 / 普通人 / 生存 / 都市 |
| `healing` | 情感疗愈 | 治愈 / 普通人 / 情感 / 都市 |

点卡片后仍生成 `theme_code=matrix` + `rule_params`；`preset_theme_code` 仅作 UI 标签。

---

## emotion 底稿参数（合成起点）

| emotion | 反转密度 | 8节点曲线 |
|---------|---------|-----------|
| revenge | 0.35 | 3→2→1→4→7→8→9→10 |
| love | 0.25 | 5→4→6→5→7→8→9→10 |
| healing | 0.15 | 4→3→4→5→5→6→7→8 |
| suspense | 0.60 | 5→6→5→7→6→8→9→10 |
| ambition | 0.45 | 3→2→5→4→7→6→9→10 |

identity / conflict / world 在此基础上加减（见 `theme-matrix.yaml`）。


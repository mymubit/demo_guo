# Catalog 原子化规范

> **状态**：Phase A/B/C 已实现（Theme + CreationForm 7 子表 + ReviewScoring 三表 + 迁移命令 + 双读）。

将 Theme / CreationForm / ReviewScoring / Hook / Dialogue 从「大 JSON blob」拆为可独立编辑的原子行；兼容现有读路径。

## 2. ThemeTemplate

**现状**：`ThemeTemplate.params` JSON 含 act_ratio、emotion_curve、hook_types 等。

**策略（PDF 问题 #3）**：**双轨过渡期**

| 阶段 | 行为 |
|------|------|
| Phase A | 保留 `params`；新增列 `description`, `core_conflict_formula`, `audience_fit`, `recommended_episodes` 等镜像常用字段 |
| Phase B | 新增子表：`ThemeActRatio`, `ThemeEmotionCurve`, `ThemeHookType`, `ThemeCharacterArchetype`, `ThemeEmotionalPeakMoment`, `ThemeReversalDensity` |
| Phase C | 读：`sync_params_from_atomic_tables()` 写回 `params` cache；写：仅改子表 |

子表字段见 PDF 第二节；`theme` FK 关联 `ThemeTemplate.id`。

## 3. CreationForm

**现状**：`CreationFormOverrideConfig.overrides` + `episode_settings` JSON。

**目标子表**：

| 表 | 来源 JSON 键 |
|----|--------------|
| `CreationPlatform` | overrides.platforms |
| `CreationBudgetLevel` | overrides.budgetLevels |
| `CreationEntry` | overrides.creationEntries |
| `CreationEntryProfile` | overrides.creationEntryProfiles |
| `FormatVariant` | overrides.formatVariants |
| `CreationThemeEntry` | themes × entry 关联 |
| `EpisodeSettingsConfig` | episode_settings |

导入：`import_configs_to_db` → `migrate_creation_form_atomic` → `sync_overrides_cache`（自动）。

## 4. ReviewScoring

**现状**：`ReviewScoringConfig` + `review_scoring_defaults.py`

**目标**：

- `ReviewScoringPreset` — preset_id: standard/strict/relaxed/rhythm_first
- `ReviewScoringDimension` — format/rhythm/content/production 权重
- `ReviewGradeThreshold` — S/A/B/C/D 分数线

审查 Agent 读取 active preset。

## 5. HookLibrary / DialogueTemplate（已原子化）

**增强项**（PDF 第八节）：

| 字段 | 说明 |
|------|------|
| `theme` | FK ThemeTemplate，nullable |
| `approved_by`, `approved_at` | 官方推荐审核 |
| `use_count` | 已有；运营统计 |

**分层**：`ThemeHookType` = 题材标签层；`HookLibrary.theme` = 具体文案层 — 不合并。

## 6. 读写入口

| Catalog | 读 | 写 |
|---------|----|----|
| Theme | creation submit / form API | Admin + init_skill_data |
| Hook/Dialogue | 推荐/润色服务 | Admin |
| Form | Portal creation options | Admin |
| Scoring | review Agent Knowledge | Admin preset 切换 |

## 7. 迁移

1. `init_skill_data` 种子
2. `migrate_hardcoded_configs_to_db`
3. 原子化命令：`migrate_creation_form_atomic` / `migrate_review_scoring_atomic` / `migrate_theme_atomic` 从 JSON 拆行
4. 回归：creation submit 表单选项不变

## 8. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | 8 题材 theme_code 均可选 |
| boundary | 关闭单条 Hook is_active 后列表不出现 |
| error | params cache 与子表不一致时告警（监控） |
| permission | Catalog Admin 仅 staff |

## 9. 旧逻辑删除

- `skill_settings.py` 内 `BUILTIN_THEMES` 作为运行时 SSOT — 仅 bootstrap
- Fusion theme 注入 — 删除

参考：[10-DATA-LAYER-MAP.md](./10-DATA-LAYER-MAP.md)、[14-SKILL-CONFIG-ENTRY-MATRIX.md](./14-SKILL-CONFIG-ENTRY-MATRIX.md)。

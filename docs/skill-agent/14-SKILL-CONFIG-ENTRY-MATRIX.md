# SkillConfigEntry 对照矩阵

---

## 1. 目标

明确每个 `config_key` 是保留 JSON、迁专用表，还是迁 SkillRuleItem；`SkillConfig` 仅保留加密 KV。

## 2. SkillConfigEntry 现状

表：`skill_config_entry` — 字段 `config_key`, `edition`, `content`, `version`, `note`

API：Console `/api/configs/<config_key>/`（Cursor Agent 拉取）

## 3. config_key 矩阵

| config_key | 当前存储 | 目标态 | 专用表/说明 |
|------------|----------|--------|-------------|
| `skill-thresholds` | JSON | `EmotionEngineRule` 或 Item | releasePassScore, minSubItemScore |
| `qdn-emotion-engine` | JSON | 保留 JSON 或 EmotionEngineRule | 15 情绪权重 |
| `episode-numbering-schema` | JSON | SkillConfigEntry | 按题材编号规则 |
| `character-voice-templates` | JSON | DialogueTemplate 扩展 | 与对话模板合并 |
| `polish-rewrite-rules` | JSON | `PolishRewriteRule` 表 | 一行一条规则 |
| `skill-rules-index` | JSON | 删除运行时依赖 | 仅 import 索引 |
| `agent-node-skill-map` | JSON | **删除** | Fusion 映射，见 Legacy 计划 |

## 4. ReferenceLibraryConfig

表：`reference_library_config` — `content` 为 `{filename: parsed_json}`

| 文件键 | 用途 |
|--------|------|
| `industry-benchmarks.json` | 题材基准数据 |
| `platform-content-standards.json` | 平台标准 |
| `theme-templates.json` | 与 ThemeTemplate 同步/import |

读：Reference 服务或 Knowledge import；不直接在 runtime 读磁盘 `references/`。

## 5. SkillConfig（加密）

仅保留：

| config_key | 说明 |
|------------|------|
| `llm.api_key` | AES-256-CBC |
| `llm.base_url` | 可选加密 |

其他非敏感项 → `SkillConfigEntry` 或 `LlmProvider`。

## 6. ReviewScoring

当前：`ReviewScoringConfig`（agent app 或 skill portal）

迁移目标：见 [13-CATALOG-ATOMIC-SPEC.md](./13-CATALOG-ATOMIC-SPEC.md) Preset 三表；过渡期双读 preset_id。

## 7. 迁移命令

```bash
python manage.py migrate_hardcoded_configs_to_db
```

源文件：`review_scoring_defaults.py`, `creation_form_defaults.py`, `skill-thresholds.json` 等。

## 8. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | config API 返回 content + version |
| boundary | 未知 config_key 404 |
| error | content 非 JSON 可解析 |
| permission | 敏感 SkillConfig 不通过 API 暴露明文 |

## 9. 旧逻辑删除

- 代码内 `BUILTIN_*` 常量作为运行时 SSOT
- Fusion `config_loader.py` 磁盘读取

参考：[20-MIGRATION-RUNBOOK.md](./20-MIGRATION-RUNBOOK.md)。

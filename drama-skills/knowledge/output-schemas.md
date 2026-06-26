# 输出契约 Schema（Output Schemas）

> **SSOT**：`registry.yaml` 的 `default_output_artifact_key` + `schema_version`；字段细节以本文档与 `roles/*/role.yaml` 为准。

## schema 索引

| schema_version | 产物键 | 角色 | 格式 |
|----------------|--------|------|------|
| project-brief.v1 | project_brief | drama.topic-planner | JSON |
| market-report.v1 | market_report | drama.market-analyst | JSON |
| world-setting.v1 | world_setting | drama.world-architect | JSON / MD |
| character-bible.v1 | character_bible | drama.character-designer | JSON / MD |
| series-outline.v1 | series_outline | drama.plot-architect | JSON / MD |
| narrative-plan.v1 | narrative_plan | drama.narrative-engineer | JSON |
| episode-scripts.v1 | episode_scripts | drama.script-writer | JSON |
| review-report.v1 | review_report | drama.script-reviewer | JSON |
| quality-report.v1 | quality_report | drama.quality-reporter | JSON |
| polished-script.v1 | polished_script | drama.polish-master | JSON / MD |
| production-pack.v1 | production_package | drama.production-pack | JSON / MD |
| compliance-report.v1 | compliance_report | drama.compliance-guard | JSON |

---

## project-brief.v1（立项简报）

```json
{
  "title": "string",
  "genre_matrix": {
    "emotion": "revenge|love|healing|suspense|ambition|comedy|justice",
    "identity": "underdog|reborn|hidden-elite|ordinary|outcast|student|protector",
    "conflict": "family|workplace|romance|power|survival|crime|disparity",
    "world": "modern|ancient|republic|rural|fantasy|campus|scifi",
    "flavor_tags": ["wuxia", "nongtian", "infinite-flow", "..."],
  },
  "theme_code": "matrix",
  "matrix_key": "revenge-reborn-family-ancient",
  "rule_params": {
    "reversal_density": 0.48,
    "emotion_curve": [3, 2, 1, 4, 7, 8, 9, 10],
    "act_ratio": [0.08, 0.20, 0.25, 0.23, 0.13, 0.11],
    "hook_types": ["隐忍爆发", "先知先觉", "宫廷政变"]
  },
  "preset_theme_code": "family-revenge",
  "episode_count": 0,
  "episode_duration": 0,
  "core_idea": "string",
  "target_audience": "string",
  "core_conflict": "string",
  "hook_concept": "string",
  "commercial_hook": "string",
  "reference_works": ["string"],
  "compliance_risk": "low|medium|high"
}
```

## world-setting.v1（世界观）

```json
{
  "setting_summary": "string",
  "root_rules": ["string"],
  "core_nouns": {"term": "definition"},
  "dream_indicators": {
    "safety": "string",
    "satisfaction": "string",
    "reality": "string"
  }
}
```

## character-bible.v1（人物小传）

```json
{
  "characters": [
    {
      "name": "string",
      "role_type": "protagonist|antagonist|supporting",
      "surface_desire": "string",
      "deep_need": "string",
      "ghost": "string",
      "lie": "string",
      "flaw": "string",
      "arc": {"start": "string", "turning_point_1": "string", "turning_point_2": "string", "end": "string"}
    }
  ],
  "relationship_map": [{"from": "string", "to": "string", "type": "string"}]
}
```

## series-outline.v1（分集大纲）

```json
{
  "drama_title": "string",
  "episodes": [
    {
      "episode": 1,
      "title": "string",
      "core_event": "string",
      "emotion_intensity": 7,
      "hook_grade": "S|A|B|C",
      "characters": ["string"],
      "emotion_nodes": {
        "EV": {"time_pct": 75, "value": 9},
        "ET": {"time_pct": 20, "value": 3},
        "TP": {"time_pct": 50, "content": "string"}
      }
    }
  ]
}
```

## episode-scripts.v1（分集剧本）

见 `roles/drama-script-writer/tasks/write-episodes.md` 的 `expected_output` 样例。

## review-report.v1（审稿报告）

```json
{
  "schema_version": "review-report.v1",
  "project_basic_info": {
    "title": "string",
    "review_episode_range": "第1-3集",
    "total_checked_scene_count": 0,
    "total_checked_word_count": 0
  },
  "format_compliance_check": {
    "compliance_rate": 90,
    "pass_check_item": ["string"],
    "minor_violation_item": ["string"]
  },
  "g_eval_scoring": {
    "total_score": 85,
    "comprehensive_level": "S|A|B|C|D"
  },
  "mandatory_modification_list": [{"serial_num": 1, "content": "string"}],
  "suggested_optimization_list": [{"serial_num": 1, "content": "string"}],
  "overall_result": "通过|条件通过|需要修改|重大返工"
}
```

## quality-report.v1（质量报告）

```json
{
  "drama_title": "string",
  "overall_score": 82,
  "grade": "S|A|B|C|D",
  "dimensions": {
    "format": {"score": 88, "weight": 0.15, "notes": "string"},
    "structure": {"score": 85, "weight": 0.20, "notes": "string"},
    "character": {"score": 78, "weight": 0.15, "notes": "string"},
    "emotion": {"score": 83, "weight": 0.15, "notes": "string"},
    "dialogue": {"score": 80, "weight": 0.15, "notes": "string"},
    "hooks": {"score": 85, "weight": 0.10, "notes": "string"},
    "dream": {"score": 82, "weight": 0.05, "notes": "string"},
    "commercial": {"score": 78, "weight": 0.05, "notes": "string"}
  },
  "defects": [],
  "verdict": "通过|条件通过|需要修改|重大返工"
}
```

## compliance-report.v1（合规报告）

```json
{
  "drama_title": "string",
  "check_mode": "standard|values-risk|full",
  "overall_result": "通过|风险|不通过",
  "blocking_issues": [],
  "risk_items": [{"type": "p0|p1|p2", "description": "string", "suggestion": "string"}]
}
```

---

## 推荐交付目录（可选）

```
output/《剧名》/
├── 01_立项/project_brief.json
├── 02_设定/world_setting.md · character_bible.md · series_outline.md
├── 03_剧本/episode_scripts/
├── 04_评估/review_report.json · quality_report.json · compliance_report.json
└── 05_发行/production_package/   （可选，drama.production-pack）
```

修改字段时：同步更新本文档、对应 `role.yaml` 的 `schema_version`，并在 `EVOLUTION_LOG.md` 记录。

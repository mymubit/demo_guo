# 输出契约 Schema（Output Schemas）

> **SSOT**：`registry.yaml` 的 `default_output_artifact_key` + `schema_version`；字段细节以本文档与 `roles/*/role.yaml` 为准。

## schema 索引

| schema_version | 产物键 | 角色 | 格式 |
|----------------|--------|------|------|
| project-brief.v1 | project_brief | drama.topic-director | JSON |
| story-bible.v1 | story_bible | drama.story-bible | JSON / MD |
| narrative-plan.v1 | narrative_plan | drama.episode-designer | JSON |
| episode-scripts.v1 | episode_scripts | drama.script-writer | JSON |
| quality-report.v1 | quality_report | drama.script-scorer | JSON |
| polished-script.v1 | polished_script | drama.revision-master | JSON / MD |
| compliance-report.v1 | compliance_report | drama.compliance-guard | JSON |
| production-pack.v1 | production_package | drama.delivery-tool | JSON / MD |

> v5 变更：`story-bible.v1` = 原 `character-bible.v1` ∪ `series-outline.v1` ∪ 梗概层。
> 原 `character_bible` / `series_outline` 两个产物键作为 `story_bible` 内部分节的兼容别名保留（见 `foundation/constraints/artifact-chunk-map.yaml`）。

---

## project-brief.v1（立项简报）

```json
{
  "title": "string",
  "genre_matrix": {
    "emotion": "revenge|love|healing|suspense|ambition|comedy|justice|warmth|nostalgia",
    "identity": "underdog|reborn|hidden-elite|ordinary|outcast|student|protector|bound|dual-lead",
    "conflict": "family|workplace|romance|power|survival|crime|disparity|redemption|tradition",
    "world": "modern|ancient|republic|rural|fantasy|campus|scifi|virtual|overseas",
    "flavor_tags": ["wuxia", "nongtian", "infinite-flow", "..."]
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
  "compliance_risk": "low|medium|high",
  "market_opportunity": "string",
  "blockbuster_factors": ["string"],
  "competitor_references": [{"title": "string", "inspiration": "string", "avoidance": "string"}],
  "differentiation_strategy": "string",
  "first_episode_hook": "string",
  "paywall_direction": "string"
}
```

> 四轴枚举 SSOT：`foundation/theme-matrix.yaml`（各轴 9 项 + 69 风味标签）。
> `rule_params.act_ratio` 为题材合成值，示例仅供参考；全局基线为 10/20/20/20/15/15（`stage-playbook.yaml`）。

## story-bible.v1（故事蓝图 = 梗概层 + 人物层 + 结构层）

```json
{
  "drama_title": "string",
  "logline": "一句话故事",
  "synopsis": {
    "short": "300字短梗概",
    "full": "千字完整梗概"
  },
  "adapt_source": {
    "mode": "original|adapt",
    "retained": ["改编模式：保留的原故事要素"],
    "enhanced": ["改编模式：强化的要素"],
    "rewritten": ["改编模式：改写的要素"],
    "originality_check": "改编模式：原创性风险自检结论"
  },
  "world_rules": {
    "setting_summary": "string",
    "root_rules": ["只保留影响人物行动和剧情选择的规则"],
    "power_structure": "string"
  },
  "characters": [
    {
      "name": "string",
      "role_type": "protagonist|antagonist|supporting",
      "surface_desire": "string",
      "deep_need": "string",
      "ghost": "string",
      "lie": "string",
      "flaw": "string",
      "arc": {"start": "string", "turning_point_1": "string", "turning_point_2": "string", "end": "string"},
      "audience_identification": "string",
      "voice_tag": "string",
      "visual_anchor": "string"
    }
  ],
  "relationship_map": [{"from": "string", "to": "string", "type": "string"}],
  "series_structure": {
    "main_storyline": "string",
    "six_stage_structure": [
      {"stage": "string", "episode_range": "1-3", "function": "string", "turning_point": "string"}
    ],
    "conflict_escalation_chain": ["string"],
    "major_reversal_positions": [{"episode": 12, "content": "string"}],
    "paywall_distribution": [{"episode": 5, "hook": "string"}],
    "foreshadowing_table": [{"setup_episode": 2, "payoff_episode": 18, "item": "string"}],
    "series_emotion_curve": [{"episode": 1, "value": 7}]
  }
}
```

> 原创模式 `adapt_source.mode = "original"`，其余 adapt 字段可省略。
> 长剧分节：先产出梗概层+`world_rules`+`characters`+`relationship_map`，再补 `series_structure`（`outline_mode=structure_only`）。

## narrative-plan.v1（分集设计）

```json
{
  "episode_narrative_designs": [
    {
      "episode": 1,
      "title": "string",
      "core_event": "string",
      "goal_conflict": "string",
      "emotion_intensity": 7,
      "opening_hook": "string",
      "ending_hook": "string",
      "satisfaction_points": ["string"],
      "reversal": "string",
      "paywall_hook": "string",
      "rhythm_tag": "tight-heavy",
      "foreshadowing": {"setup": ["string"], "payoff": ["string"]},
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

每集必须包含 `memory_checkpoint`，字段 SSOT：
`foundation/constraints/continuity-checkpoint.yaml`。检查点至少包含：

- `episode`
- `character_states`
- `active_clues`
- `foreshadowing`
- `rhythm_state`
- `next_episode_constraints`

## quality-report.v1（十维评分报告）

```json
{
  "drama_title": "string",
  "scored_artifact": "polished_script|episode_scripts|external_script",
  "overall_score": 82,
  "grade": "S|A|B|C|D",
  "can_continue_next_batch": true,
  "needs_revision": true,
  "dimensions": {
    "format": {"score": 88, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "narrative": {"score": 85, "weight": 0.15, "evidence": ["string"], "deductions": ["string"]},
    "conflict": {"score": 82, "weight": 0.15, "evidence": ["string"], "deductions": ["string"]},
    "character": {"score": 78, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "emotion": {"score": 83, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "logic": {"score": 80, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "satisfaction": {"score": 84, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "hooks": {"score": 85, "weight": 0.10, "evidence": ["string"], "deductions": ["string"]},
    "paywall": {"score": 78, "weight": 0.05, "evidence": ["string"], "deductions": ["string"]},
    "genre_fit": {"score": 82, "weight": 0.05, "evidence": ["string"], "deductions": ["string"]}
  },
  "defects": [],
  "revision_priorities": [{"priority": 1, "target": "string", "suggestion": "string"}],
  "evolution_proposal": {"trigger": "同一维度连续2次<70", "target": "foundation/rules/...", "content": "string"},
  "verdict": "通过|条件通过|需要修改|重大返工"
}
```

> `evolution_proposal` 仅在触发进化条件时输出，路由至 `@drama-intake` 轨道一。

## compliance-report.v1（合规报告）

```json
{
  "drama_title": "string",
  "check_mode": "standard|values-risk|full",
  "checked_artifact": "polished_script|episode_scripts|external_script",
  "overall_result": "通过|风险|不通过",
  "blocking_issues": [],
  "risk_items": [{"type": "p0|p1|p2", "description": "string", "suggestion": "string"}]
}
```

---

## 推荐交付目录（可选）

```
output/《剧名》/
├── 01_立项/project_brief.json          （原创通道）
├── 02_蓝图/story_bible.json
├── 03_分集/narrative_plan.json
├── 04_剧本/episode_scripts/ · polished_script/
├── 05_质检/quality_report.json · compliance_report.json
└── 06_宣发/production_package/         （可选，drama.delivery-tool）
```

修改字段时：同步更新本文档、对应 `role.yaml` 的 `schema_version`，并在 `EVOLUTION_LOG.md` 记录。

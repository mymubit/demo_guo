# 输出契约 Schema（Output Schemas）

> **机器 SSOT**：`schemas/artifacts/<artifact_key>/1.schema.json`。
> **Prompt 字段表**：运行时由 `schema_prompt_contract` 从 schema 生成，禁止在 prompt_builder 手写第二份必填清单。
> 本 Markdown 仅供人读；若与 schema 冲突，以 schema 为准。

## schema 索引

| artifact_key | schema_version | 中文标签 | 角色 | 格式 |
|--------------|----------------|----------|------|------|
| project_brief | 1 | 立项简报 | drama.topic-director | JSON |
| story_bible | 1 | 故事蓝图 | drama.story-bible | JSON / MD |
| narrative_plan | 1 | 分集设计 | drama.episode-designer | JSON |
| episode_scripts | 1 | 分集剧本 | drama.script-writer | JSON |
| quality_report | 1 | 质量评分报告 | drama.script-scorer | JSON |
| polished_script | 1 | 修复稿 | drama.revision-master | JSON / MD |
| compliance_report | 1 | 合规审查报告 | drama.compliance-guard | JSON |
| production_package | 1 | 制作发行交付包 | drama.delivery-tool | JSON / MD |
| memory_checkpoint | 1 | 连续性检查点 | （内嵌于 episode_scripts） | JSON |

`story_bible` 是人物、世界规则与全剧结构的唯一蓝图产物。
`latest_script` 是不持久化的虚拟输入，由 `contracts/artifacts.yaml` 在当前批次解析为有效剧本。

---

## project_brief（立项简报 · v1）

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

## story_bible（故事蓝图 · v1）

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

## narrative_plan（分集设计 · v1）

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

## episode_scripts（分集剧本 · v1）

见 `roles/drama-script-writer/tasks/write-episodes.md` 的 `expected_output` 样例。

每集必须包含 `memory_checkpoint`，字段 SSOT：
`foundation/constraints/continuity-checkpoint.yaml`。检查点至少包含：

- `episode`
- `character_states`
- `active_clues`
- `foreshadowing`
- `rhythm_state`
- `next_episode_constraints`

每集同时输出 `production_notes`，字段读取
`foundation/constraints/production-feasibility.yaml#required_output`。

## quality_report（十维评分报告 · v1）

```json
{
  "drama_title": "string",
  "scored_artifact": "latest_script",
  "resolved_script_key": "polished_script|episode_scripts|external_script",
  "scoring_preset": "standard|strict|relaxed|rhythm_first",
  "pass_threshold": 75,
  "config_revision": "string",
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
  "continuity_summary": {
    "result": "pass|warning|fail",
    "issues": [{"episodes": [1, 2], "facts": ["string"], "responsible_layer": "script|checkpoint|blueprint"}]
  },
  "revision_priorities": [{"priority": 1, "target": "string", "suggestion": "string"}],
  "evolution_proposal": {"trigger": "同一维度连续2次<70", "target": "foundation/rules/...", "content": "string"},
  "verdict": "通过|条件通过|需要修改|重大返工"
}
```

> `evolution_proposal` 仅在触发进化条件时输出，路由至 `@drama-intake` 轨道一。

## compliance_report（合规报告 · v1）

```json
{
  "drama_title": "string",
  "check_mode": "standard|values-risk|full",
  "target_platform": "generic|douyin|kuaishou|wechat_miniprogram",
  "platform_policy_version": "string|null",
  "platform_policy_verified_at": "string|null",
  "checked_artifact": "latest_script",
  "resolved_script_key": "polished_script|episode_scripts|external_script",
  "overall_result": "通过|风险|不通过",
  "blocking_issues": [],
  "risk_items": [{"type": "p0|p1|p2", "description": "string", "suggestion": "string"}]
}
```

---

## production_package（制作发行交付包 · v1）

```json
{
  "drama_title": "string",
  "source_artifact": "latest_script",
  "storyboard": [],
  "visual_assets": [],
  "marketing_assets": [],
  "interactive_adaptation": null,
  "production_plan": {
    "complexity_score": 0,
    "complexity_band": "lean|standard|complex",
    "cost_drivers": [],
    "high_cost_scenes": [],
    "lower_cost_alternatives": [],
    "budget_range": null,
    "pricing_context": null
  },
  "release_checklist": {
    "target_platform": "generic|douyin|kuaishou|wechat_miniprogram",
    "policy_version": "string|null",
    "verified_at": "string|null",
    "blocking_items": [],
    "missing_materials": [],
    "can_release": false
  }
}
```

金额预算仅在地区、币种、价格版本和排除项齐全时允许填写。

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

修改字段时：同步更新 `contracts/artifacts.yaml`、对应 Schema 文件，并在 `EVOLUTION_LOG.md` 记录。

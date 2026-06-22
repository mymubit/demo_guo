# 输出契约 Schema（Output Schemas）

> **来源**：dramaskill `schemas/` 目录（16个JSON Schema文件）
> 
> **使用方式**：
> - AI工具创作时确保输出结构正确
> - 网站集成时定义API响应类型
> - 前端TypeScript类型生成参考

---

## 核心输出文件契约

### 1. project-brief（立项简报）

```json
{
  "title": "string",              // 暂定剧名
  "theme_code": "string",         // 题材代码（见theme-templates.md）
  "episode_count": "number",      // 总集数
  "episode_duration": "number",   // 单集时长（分钟）
  "core_idea": "string",          // 一句话核心创意（<50字）
  "target_audience": "string",    // 目标受众画像
  "core_conflict": "string",      // 核心冲突定义
  "hook_concept": "string",       // 开篇钩子方案
  "commercial_hook": "string",    // 商业卖点（<30字）
  "reference_works": ["string"],  // 参考对标作品
  "compliance_risk": "low|medium|high"  // 合规风险预判
}
```

### 2. structure-plan（结构规划）

```json
{
  "drama_title": "string",
  "total_episodes": "number",
  "act_ratio": [0.10, 0.20, 0.25, 0.20, 0.15, 0.10],  // 6阶段比例
  "stages": [
    {
      "stage": 1,
      "name": "string",
      "episode_range": [1, 8],
      "core_event": "string",
      "emotion_intensity": [3, 6]  // [起始值, 结束值]
    }
  ],
  "worldview": {
    "setting_summary": "string",
    "root_rules": ["string"],
    "core_nouns": {"string": "string"},
    "dream_indicators": {
      "safety": "string",
      "satisfaction": "string",
      "reality": "string"
    }
  },
  "emotion_curve": [3, 2, 1, 4, 7, 8, 9, 10]  // 8节点
}
```

### 3. character-bible（人物小传）

```json
{
  "characters": [
    {
      "name": "string",
      "role_type": "protagonist|antagonist|supporting",
      "age": "number",
      "gender": "M|F",
      "occupation": "string",
      "surface_desire": "string",
      "deep_need": "string",
      "core_fear": "string",
      "character_flaw": "string",
      "arc": {
        "start": "string",
        "turning_point_1": "string",
        "turning_point_2": "string",
        "end": "string"
      },
      "voice_tag": {
        "tone": "string",
        "speed": "fast|medium|slow",
        "emotion_base": "string"
      },
      "signature_line": "string"
    }
  ],
  "relationship_map": [
    {
      "from": "string",
      "to": "string",
      "type": "string",
      "initial": "string",
      "final": "string"
    }
  ]
}
```

### 4. series-outline（分集大纲）

```json
{
  "drama_title": "string",
  "episodes": [
    {
      "episode": 1,
      "title": "string",
      "core_event": "string",
      "emotion_intensity": 7,
      "segments": {
        "hook": "string",
        "setup": "string",
        "escalation": "string",
        "cliffhanger": "string"
      },
      "emotion_nodes": {
        "EV": {"time_pct": 75, "value": 9, "trigger": "string"},
        "ET": {"time_pct": 20, "value": 3, "trigger": "string"},
        "TP": {"time_pct": 50, "content": "string"}
      },
      "hook_type": "string",
      "hook_grade": "S|A|B|C",
      "characters": ["string"],
      "gold_line": "string"
    }
  ]
}
```

### 5. quality-report（质量报告）

```json
{
  "drama_title": "string",
  "report_date": "YYYY-MM-DD",
  "version": "string",
  "scoring_preset": "standard|strict|relaxed|rhythm_first",
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
  "defects": [
    {
      "id": "D001",
      "dimension": "character",
      "location": "string",
      "description": "string",
      "severity": "high|medium|low",
      "suggestion": "string",
      "fix_owner": "string"
    }
  ],
  "verdict": "通过|条件通过|需要修改|重大返工",
  "next_step": "string",
  "blocking_issues": []
}
```

### 6. compliance-report（合规报告）

```json
{
  "drama_title": "string",
  "check_mode": "standard|values-risk|full",
  "overall_result": "通过|风险|不通过",
  "compliance_score": 92,
  "blocking_issues": [],
  "risk_items": [
    {
      "type": "p0|p1|p2",
      "location": "string",
      "description": "string",
      "severity": "critical|high|medium|low",
      "suggestion": "string"
    }
  ],
  "values_risk": {
    "overall_label": "低风险|中风险|高风险",
    "crime_justice": "已有收束|需要补充|无犯罪内容"
  },
  "platform_fit": {
    "douyin": "通过|风险|不通过",
    "kuaishou": "通过|风险|不通过",
    "weixin": "通过|风险|不通过"
  }
}
```

---

## 文件路径规范

```
output/《剧名》/
├── 02_项目设定/
│   ├── 世界观设定.md         → structure-plan.worldview
│   ├── 人物小传.md            → character-bible
│   └── 分集大纲.md            → series-outline
├── 03_完整剧本/
│   └── 第X集.md              → episode-scripts（纯剧本，无设定）
├── 04_评估报告/
│   └── 质量报告.json          → quality-report schema
└── 《剧名》交付包.md          → 02+03全量合并
```

---

## 网站API集成建议

每个角色的 `input_schema` 和 `output_schema` 可直接映射为：
- 后端 DRF Serializer 字段定义
- 前端 TypeScript interface
- API 请求/响应体结构

详见各 SKILL.md 的 YAML frontmatter 中的 `input_schema` / `output_schema` 字段。

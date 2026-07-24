# W4 Task 2 Brief

Plan: docs/superpowers/plans/2026-07-23-drama-website-v3-w4-quality-delivery.md

### Task 2: recipe_map + fixtures + validate

**Files:**
- Modify: `skills_bridge/recipe_map.py`
- Create fixtures:
  - `backend/apps/drama/tests/fixtures/v3_quality_report.json`
  - `v3_compliance_report.json`
  - `v3_production_package.json`
- Test: 扩展 `test_v3_skills_bridge.py` 或新建 `test_v3_quality_recipes.py`

**Recipes (verbatim):**

```python
"score_quality": {
    "recipe_id": "score-script",
    "role": "drama-score-critic",  # align with skills; verify against operation/SKILL
    "writes": ["quality_report"],
    "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
    "commit_mode": "direct",
},
"check_compliance": {
    "recipe_id": "check-compliance",
    "role": "drama-compliance-guard",
    "writes": ["compliance_report"],
    "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
    "commit_mode": "direct",
},
"revise_from_findings": {
    "recipe_id": "revise-script",
    "role": "drama-revision-master",
    "writes": ["episode_scripts", "memory_checkpoint"],
    "requires_committed": ["episode_scripts", "episode_plan", "story_bible"],
    "commit_mode": "candidate",
},
"prepare_delivery": {
    "recipe_id": "prepare-delivery",
    "role": "drama-delivery-tool",
    "writes": ["production_package"],
    "requires_committed": ["episode_scripts", "quality_report", "compliance_report"],
    "commit_mode": "direct",
    "requires_delivery_gate": True,
},
```

Fixtures MUST pass `validate_artifact_payload` (minimal legal fields; 10 quality dimensions each with score/weight/evidence/deductions).

Schemas:
- drama-skills/schemas/artifacts/quality_report/1.schema.json
- compliance_report/1.schema.json
- production_package/1.schema.json

Do NOT implement executor/gate yet (Task 3).
Do NOT git commit.

## Global Constraints
- No v6_* imports
- No new deps
- Work: c:\Users\99193\Desktop\demo_guo
- Tests: py -3 manage.py test … --settings=config.settings.sqlite_test
- DRAMA_SKILLS_ROOT=c:\Users\99193\Desktop\demo_guo\drama-skills

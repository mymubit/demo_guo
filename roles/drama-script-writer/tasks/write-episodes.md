# 任务：生成指定集数剧本

## 输入
- `params.episode_range`：如 `1-5`（必填，严禁一次生成全剧）
- 上游：`story_bible`（人物层 + 结构层）
- 必填：`narrative_plan`（严格遵循 EV/ET、钩子与冲突安排）
- 可选：`project_brief`

## 执行步骤
1. 确认 episode_range，只生成范围内集数
2. 按 `script-format.yaml` 的场景数约束拆场，第 1 集第一场从最大张力横截面切入
3. 每场戏验证 Goal×Conflict 与 McKee 价值转变
4. 每集完成后输出 memory_checkpoint
5. 每集输出字数、台词占比、格式自检、可传播金句与 production_notes
6. 输出合法 JSON，遵循 `episode-scripts.v1`

## 数值约束
字数、台词占比和场景数只读取 `foundation/constraints/script-format.yaml`，不得在任务中复制数值。
`memory_checkpoint` 读取 `foundation/constraints/continuity-checkpoint.yaml`。

## expected_output
```json
{
  "episodes": [
    {
      "episode_number": 1,
      "title": "集标题",
      "script": "完整剧本文本",
      "word_count": 850,
      "dialogue_ratio": 0.38,
      "scene_count": 2,
      "memory_checkpoint": {"episode": 1, "character_states": [], "active_clues": [], "foreshadowing": [], "rhythm_state": {}, "next_episode_constraints": []},
      "production_notes": {"tags": [], "complexity_score": 0, "complexity_band": "lean", "high_cost_scenes": [], "lower_cost_alternatives": []}
    }
  ]
}
```

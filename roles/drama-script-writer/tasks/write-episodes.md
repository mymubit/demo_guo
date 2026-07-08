# 任务：生成指定集数剧本

## 输入
- `params.episode_range`：如 `1-5`（必填，严禁一次生成全剧）
- 上游：`story_bible`（人物层 + 结构层）
- 可选：`narrative_plan`（若有则严格遵循 EV/ET、钩子与冲突安排）、`project_brief`

## 执行步骤
1. 确认 episode_range，只生成范围内集数
2. 每集 1–3 场景，第 1 集第一场从最大张力横截面切入
3. 每场戏验证 Goal×Conflict 与 McKee 价值转变
4. 每集完成后输出 memory_checkpoint
5. 每集输出字数、台词占比、格式自检和可传播金句
6. 输出合法 JSON，遵循 `episode-scripts.v1`

## 数值约束
引用 `foundation/constraints/script-format.yaml`：
- 第 1 集 900–1100 字，其余 700–900 字
- 台词占比 ≥ 35%
- 每集场景数 1–3

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
      "memory_checkpoint": {}
    }
  ]
}
```

# 结构化输出护栏（技能知识）

> 供 PromptBuilder 轻量注入；与 `roles/*/anti-examples.yaml` 互补。

## 通用禁止

1. 不要输出 markdown 代码围栏或解释性前后缀。
2. 不要输出 `artifact_key`、`schema_version` 等元数据字段。
3. 枚举字段必须使用 schema 给定英文/中文枚举字面量，不要同义改写。

## project_brief

- `blockbuster_factors`：字符串数组，不要 `{factor, description}` 对象。
- `compliance_risk`：仅 `low|medium|high`。
- 不要输出 `rule_params`（系统合成）。

## story_bible

- `synopsis` 必须是 `{short, full}` 对象，禁止纯字符串。
- `characters[].role_type`：仅 `protagonist|antagonist|supporting`。
- `series_structure.six_stage_structure`：恰好 6 项。

## 平台提示（摘要）

- `douyin`：开场留存敏感，前 3 秒避免高风险内容。
- `kuaishou`：未成年人场景更严格。
- `wechat_miniprogram`：注意备案与 AI 内容标识要求。

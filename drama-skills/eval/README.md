# Drama Skills 角色 LLM 评测

自建评测（不依赖 Promptfoo）。先离线用 fixture 响应做 schema/rubric 回归，再按需在线调用模型。

## 目录

- `cases/<role-slug>/*.yaml` — 单条 case
- `rubrics/*.yaml` — 产物级启发式 rubric
- `reports/` — 运行报告（大文件 gitignore，保留 summary）

## 运行

```bash
# 离线（默认）：用 case.fixture_response 或 valid-artifacts 回放
python build/eval_role_llm.py --roles topic-director,story-bible --offline
python build/eval_role_llm.py --roles script-scorer,compliance-guard --offline
```

## Case 字段

| 字段 | 说明 |
|------|------|
| `id` | 如 TD001 |
| `role` | agent_id |
| `settings` | 内联项目设置子集 |
| `upstream_artifacts` | 上游产物 |
| `fixture_response` | 离线响应（对象）；缺省则用 valid-artifacts 对应产物 |
| `assertions.schema` | 是否做 schema 校验 |
| `assertions.required_fields` | 路径非空检查 |
| `assertions.rubric` | 引用 rubrics 中的检查项 id 列表 |

# 模型/供应商分版的技能优化产物（人工审阅后合并）

目录约定：

```
optimizations/<provider-or-model>/<role-slug>/fewshots.v1.yaml
```

示例：`optimizations/generic/topic-director/fewshots.v1.yaml`

生成：

```bash
python build/optimize_role_dspy.py --role topic-director --write
python build/optimize_role_dspy.py --role story-bible --write
```

禁止脚本直接覆盖 `roles/*/SKILL.md`。

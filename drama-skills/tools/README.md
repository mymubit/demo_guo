# tools/ · 工具链

> 校验 / 生成 / 优化脚本的唯一入口（原 `build/` 已硬删）。

| 目录 | 用途 | 示例 |
|------|------|------|
| `validators/` | CI / 一致性校验 | `validate_all.py`、`validate_skills.py` |
| `generators/` | 契约生成 / 导出 | `generate_parameter_schemas.py` |
| `optimizers/` | 低频优化 / 一次性脚本 | `slim_skill_bodies.py`、`fix_yaml_headers.py` |
| `lib/` | 公共库 | `condition_eval.py`、`contracts_loader.py` |
| `fixtures/` | 校验用样例 | `artifacts/`、`config/`、`workflow/` |
| `tests/` | 工具链单测 | `test_runtime.py` |

## 推荐命令

```bash
# 在 drama-skills 根目录
python tools/validators/validate_all.py
python -m unittest discover -s tools/tests -p "test_*.py" -v
python eval/tools/eval_role_llm.py --roles topic-director,story-bible --offline
```

## 刻意未搬

| 项 | 理由 |
|----|------|
| `drama-master/` / `drama-intake/` | C1 已记 P2，入口收敛另开 |
| `runtime/` | 双引擎以 backend 为准，搬家风险高 |
| `optimizations/`（fewshot 产物） | 非脚本；进化轨瘦身属阶段 E |

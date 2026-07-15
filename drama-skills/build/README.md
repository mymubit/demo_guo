# build/ 维护脚本

| 脚本 | 用途 |
|------|------|
| `generate_role_skeletons.py` | 从 registry 生成角色目录骨架 |
| `slim_skill_bodies.py` | 将 SKILL.md 瘦身为索引文档 |
| `fix_yaml_headers.py` | 统一 rules/*.yaml 首行 scope 注释 |
| `synthesize_matrix_params.py` | 四轴 genre_matrix → rule_params 合成（校验用） |
| `validate_theme_matrix.py` | 校验 theme-matrix 轴/标签/deltas 完整性 |
| `validate_skills.py` | 全库一致性校验（registry ↔ roles ↔ orchestration ↔ rules ↔ references） |
| `validate_workbench.py` | 工作台、角色参数与后台策略校验 |
| `validate_artifacts.py` | 产物 JSON Schema、样例与跨字段语义校验 |
| `validate_config.py` | 配置覆盖、条件表达式、派生与投影校验 |
| `validate_workflow.py` | 流程状态机、并发、幂等与 latest_script 校验 |
| `validate_quality_cases.py` | 质量、合规、连续性、制片和趋势回归 |
| `export_workbench_schema.py` | 导出前端可消费的工作台表单 JSON |

全量回归：

```bash
python build/validate_skills.py
python build/validate_theme_matrix.py
python build/validate_workbench.py
python build/validate_artifacts.py
python build/validate_config.py
python build/validate_workflow.py
python build/validate_quality_cases.py
python -m unittest discover -s build/tests -p "test_*.py" -v
```

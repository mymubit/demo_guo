# build/ 维护脚本

| 脚本 | 用途 |
|------|------|
| `generate_role_skeletons.py` | 从 registry 生成角色目录骨架 |
| `slim_skill_bodies.py` | 将 SKILL.md 瘦身为索引文档 |
| `fix_yaml_headers.py` | 统一 rules/*.yaml 首行 scope 注释 |
| `synthesize_matrix_params.py` | 四轴 genre_matrix → rule_params 合成（校验用） |
| `validate_theme_matrix.py` | 校验 theme-matrix 轴/标签/deltas 完整性 |
| `validate_skills.py` | 全库一致性校验（registry ↔ roles ↔ orchestration ↔ rules ↔ references） |

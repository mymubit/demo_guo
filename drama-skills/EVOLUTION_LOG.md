# Drama Skills 进化日志

> 记录 v3.1 技能库的四轨道进化。提交外部内容见 `INTAKE_PROTOCOL.md`。

## 四轨道

| 轨道 | 触发 | 写入位置 |
|------|------|----------|
| 规则进化 | 评分/审查反复暴露同一问题 | `foundation/rules/*.yaml`（PR） |
| 灵感归档 | 创作中发现好钩子/反转/对白 | `inspirations/` |
| 外部摄入 | 用户提交 PDF/文章/剧本 | `knowledge/` + `foundation/rules/` |
| 新模式 | 拉片/摄入发现库中无覆盖规律 | `inspirations/new-patterns.md` |

## v3.1 基线（2026-06-25）

- **架构**：`registry.yaml` + `roles/*/role.yaml` + `foundation/rules/` 三层 SSOT
- **角色**：12 个（8 core + 4 composite），见 `registry.yaml`
- **规则**：四 Scope（global_core / genre_profile / stage_playbook / compliance_block）
- **编排**：`orchestration/fast-track.yaml`、`expert-track.yaml`
- **题材**：`foundation/rules/genres/` 8 题材 + hybrid
- **经验规则**：`learned-rules.yaml` LR-001～LR-010

## 变更记录

### 2026-06-25 · 题材矩阵 v1.4

- 风味标签 48→69（12 类：赛博朋克/末世/竖屏互动/年代重生/黑帮/互换身体等）
- featured_combos 20→32；新增 `topic_planner_inference` 关键词推断
- 新增 `build/validate_theme_matrix.py`

### 2026-06-25 · 题材矩阵全量覆盖 v1.3

- 四轴扩至 9×9×9×9（6561 骨架组合）
- 风味标签 48 项 / 10 类，最多选 5
- 创新组合 featured_combos 扩至 20 条
- 约定：高分新组合 → `inspirations/new-patterns.md` 归档驱动进化

### 2026-06-25 · 四轴扩展 7+7+7+7 + 风味标签层

- 每轴 5→7 项（喜剧/正义、青春/守护、罪案/阶级、校园/科幻等）
- 新增 `flavor_tags`（18 项，最多选 3）覆盖武侠/修仙/医疗/无限流等长尾
- `synthesize_matrix_params.py` 支持 flavor_tags 叠加

### 2026-06-25 · 四轴直驱规则参数（废弃 archetype 硬映射）

- 四轴路径：`theme_code=matrix` + `rule_params` 由 `param_synthesis` 合成
- 8 预设降为「快捷卡片」，不再 weighted_score 映射
- 新增 `foundation/rules/genres/matrix.yaml`、`build/synthesize_matrix_params.py`

### 2026-06-25 · 四轴矩阵与规则模板对齐

- 新增 `foundation/theme-matrix.yaml`（创作层 SSOT + matrix_affinity 映射）
- `theme-templates.md` 重定位为「8 规则模板 + hybrid」，与四轴解耦说明
- `project-brief.v1` 增加 `genre_matrix` 字段

### 2026-06-25 · 阶段规则文档重命名

- `knowledge/tier3-node-rules.md` → `tier3-stage-rules.md`（去除 Node 旧命名）
- `stage-playbook.yaml` 中 `scope_type: node` → `scope_type: agent`

### 2026-06-25 · SKILL frontmatter 统一

- 移除全部 `tier` / `is_fast_track` / `merges` / `is_composite` 字段
- composite 角色改用 `modules:` 列表（与 `role.yaml` 对齐）
- `drama-intake` 路由表对齐 `INTAKE_PROTOCOL.md`（规则写入 `foundation/rules/`）
- 清理 `tier4-compliance.md`、`inspirations/` 中旧角色名引用

### 2026-06-25 · 文档与仓库瘦身

- 移除应用层代码，本目录为唯一 SSOT
- 统一全部文档至 v3.1 术语（无后端/dept/旧角色体系引用）
- `SKILL.md` 仅保留 Cursor 入口；规则全部在 `foundation/rules/`

### 2026-06-25 · 规则补全

- 新增 `learned-rules.yaml`、`conflict-escalation.yaml`、`genres/hybrid.yaml`
- 扩展 plot-architect / narrative-engineer / script-writer 的 section 覆盖

---

*后续变更请在本文件顶部「变更记录」追加条目。*

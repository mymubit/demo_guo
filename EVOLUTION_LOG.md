# Drama Skills 进化日志

> 记录技能库的四轨道进化。四轨道唯一定义见 `drama-intake/SKILL.md`；提交外部内容见 `INTAKE_PROTOCOL.md`。

## 四轨道（引用 drama-intake 定义）

| 轨道 | 名称 | 触发 | 写入位置 |
|------|------|------|----------|
| 一 | 规则进化 | 方法论/阈值/LR 提案；评分维度连续 2 次 <70 | `foundation/rules/*.yaml` |
| 二 | 灵感归档 | 创作中发现好钩子/反转/对白/结构 | `inspirations/` |
| 三 | 市场知识 | 行业数据/平台趋势/受众分析 | `knowledge/market/market-insights.md` |
| 四 | 新模式发现 | 库中无覆盖的新规律（3+ 案例验证后经轨道一升格） | `inspirations/new-patterns.md` |

## v5.0 基线（2026-07-02）

- **角色**：8 个 = 4 主链生产（topic-director / story-bible / episode-designer / script-writer）+ 3 质检环独立技能（script-scorer / compliance-guard / revision-master）+ 1 可选工具（delivery-tool）
- **编排**：双通道 `orchestration/original-track.yaml`（原创）/ `story-adapt-track.yaml`（故事改编），在 story_bible 汇合
- **质检环**：每批正文后评分+合规并行；低于 B 级（75）或 P1 → 修复 → 强制复评
- **规则**：四 Scope 不变（global_core / genre_profile / stage_playbook / compliance_block）

## 变更记录

### 2026-07-14 · 五阶段可执行契约与回归体系

- **产物 Schema**：8 类业务产物与 memory checkpoint 全部具备 JSON Schema、合法样例和非法输入回归
- **配置解析**：实现后台白名单覆盖、条件表达式、项目参数投影、版本审计和追加式回滚参考实现
- **流程状态机**：实现双通道、蓝图审批、并行质检、修复收敛、幂等、乐观锁和 latest_script 解析
- **工作台交付**：新增表单 JSON 导出器和 API 契约；实际页面由 ScriptForge 网站消费
- **质量回归**：新增15个确定性 golden cases、标准库单元测试和 GitHub Actions 门禁

### 2026-07-14 · 最新态净化与生产基建补全

- **零兼容运行时**：删除3个兼容模块、旧题材规则包、旧产物别名和双份 params 列表
- **统一当前剧本**：评分、合规、修复和交付只消费 `latest_script` 虚拟产物
- **创作基建补全**：新增世界规则、首稿对白、制片可拍性和连续性终审
- **制作发行补全**：新增预算分级、平台上架清单和制片复杂度后台配置
- **角色数保持8**：新增能力均有清晰归属和既有产物，无需为恢复历史数量制造微角色

### 2026-07-14 · 角色技能组合与工作台配置契约

- **角色组合落地**：11 个 foundation 模块正式挂载主链角色，正文官补齐场景写作与连续性快照
- **职责校正**：九列分镜从修复官迁至交付工具；修复官支持基于最新修复稿继续迭代，并读取蓝图/分集防止越界
- **参数结构化**：8 个角色的运行参数增加类型、枚举、必填条件与 UI 元数据
- **工作台契约**：新增项目设置分组、阶段导航、模块面板和后台设置来源；主题、集数、平台与质量偏好可直接生成表单
- **后台边界**：新增路径级 overlay 白名单，角色、规则、编排、题材枚举与产物契约保持 Git 只读
- **编排门禁**：蓝图人工确认、分集前置产物、结构化质检条件、最多三轮修复和异常趋势停机进入机器契约

### 2026-07-14 · 底层原子规则重新抽取与基础能力补全

- **分层固定**：knowledge 仅保留知识原料；constraints 维护数值与结构；rules 维护原子规则；modules 只组合执行流程
- **数值收敛**：新增商业公式、结构缩放、十维评分预设、连续性检查点和平台配置入口；清除题材模板、评分和格式中的重复阈值
- **规则补全**：新增概念形成、全剧结构/分集卡/连续性、原创性规则；扩展合规、人物和场景写作规则
- **模块补全**：新增概念、改编原创性、人物、全剧结构、情绪、反转伏笔、分集卡、付费卡点、场景写作和连续性快照等基础模块
- **校验增强**：新增模块目录、原子规则唯一性/SSOT方向、十维预设权重和流式产物定义校验

### 2026-07-02 · v5.1 底层技能深度治理（模块充实 + 规则合并 + 知识分目录 + 配置分级）

- **模块去空心化**：16 个 modules 从 3 行存根充实为「目标/执行步骤/量化标准/自检清单」结构的可执行操作指南（30-60 行/个），并标注挂载角色与数值 SSOT
- **规则文件合并（17→12，运行时透明）**：dialogue-voice+ai-tone-forbidden→`dialogue-rules.yaml`；writing-requirements+writing-prohibitions→`writing-rules.yaml`；conflict-escalation+foreshadowing-rules+payment-checkpoint→`plotting-rules.yaml`；character-logic→`character-rules.yaml`（扩充密度/弧光条目）；genre-profile fallback 强化为可执行摘要+默认参数；rule_key/section 全部保留
- **规则 body 治理**：可执行内容内联进 body，knowledge 指针降级为「长文参考」注释（规则条目是 prompt 实际载体，指针背后的内容运行时读不到）
- **knowledge 按消费场景分 5 目录**：craft/（创作方法论）、market/（时效市场数据，后台配置候选）、quality/（质检标准）、production/（制作宣发）、system/（流程控制）；`knowledge-sections.md`、`output-schemas.md` 留在根目录（后端固定路径解析）；全库引用路径同步更新
- **配置分级标注**：constraints 文件头部声明 `config_tier`——agent-runtime=seed_default（后台 drama-models 可覆盖）；quality-scoring 的阈值/熔断与 script-format 的字数/占比=seed_default（建议后台 system_config 覆盖）；格式 pattern、chunk-map=git_ssot
- **校验器升级**：`validate_skills.py` 新增 knowledge 孤儿检测、模块孤儿检测、全库相对路径引用有效性、角色↔Section 映射存在性 4 项检查
- 完整方案与后台配置中心设计见 `docs/DRAMA-SKILLS-V5-PLAN.md`

### 2026-07-02 · v5.0 主链收缩 + 双通道 + 质检环 + 进化机制补全

- **角色 9→8**：`drama.character-relations` + `drama.series-architect` 合并为 `drama.story-bible`（剧本蓝图官，双模式：原创/改编），modules 与 sections 全量随迁，能力零丢失（映射见 `ROLE-DESIGN-ANALYSIS.md`）
- **新产物** `story-bible.v1` = character-bible.v1 ∪ series-outline.v1 ∪ 梗概层；旧两键保留为兼容别名（`artifact-chunk-map.yaml`）
- **修复主链断链**：评分官/合规官输入改为 `required_artifacts_any_of`（polished_script > episode_scripts > external_script），修复稿强制复评
- **编排重写**：`fast-track.yaml` / `expert-track.yaml` / `ip-adapt.yaml` → `original-track.yaml` + `story-adapt-track.yaml`（expert 与 fast 的差异由 optional_agents 表达；ip-adapt 由改编通道真正实现）
- **阈值收敛**：B 级统一为 75（`quality-scoring.yaml` SSOT）；`s-class-standards.md`、`scoring-presets.md` 对齐
- **进化机制补全**：四轨道统一定义收敛至 `drama-intake/SKILL.md`（修复三处编号互相矛盾）；评分官新增进化提案规则（stage-playbook `t3.drama-script-scorer.scoring.evolution-proposal`）；`quality-report.v1` 增加 `evolution_proposal` 字段
- **stage-playbook 补缺**：新增 compliance-guard（合规裁判边界）与 delivery-tool（交付前置门禁）条目
- **知识库清理**：15+ 处旧角色名引用（topic-planner / market-analyst / quality-reporter / script-reviewer / hook-designer / ip-adapter / game-adapter / rhythm-designer / storyboard-director 等）全部改指 v5 角色；孤儿长文挂接到对应角色 SKILL references（s-class-standards / scoring-presets → 评分官；douyin-formulas / industry-benchmarks / market-insights → 选题官；originality-rules / 山音编剧长文 → 蓝图官；导演方法论 → 修复官/交付工具；story-to-game → 交付工具）
- **新增校验**：`build/validate_skills.py` 全库一致性校验（registry ↔ roles ↔ orchestration ↔ rules ↔ references）

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

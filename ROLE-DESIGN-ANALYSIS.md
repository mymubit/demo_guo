# 角色设计说明（v5.0）

> 本文档说明当前「4 主链 + 3 质检 + 1 工具」角色体系的设计 rationale。配置 SSOT：`registry.yaml` + `roles/*/role.yaml`。

## 设计目标

1. **对齐用户心智**：主链收缩为「选题 → 剧本蓝图 → 分集梗概 → 分集剧本」四步，与主流商业创作产品一致
2. **双入口汇合**：原创（从选题起）与故事改编（用户自带故事）两条通道在 `story_bible` 汇合，下游完全复用
3. **质检独立成环**：评分/合规/修复不占主链位，作为独立技能在每批正文后成环把关，且修复稿必须复评
4. **规则集中治理**：角色薄、规则厚；方法论不在 SKILL 正文重复，统一走 `foundation/rules/` + `knowledge/`

## 角色分层

| 类型 | 数量 | 角色 |
|------|------|------|
| 主链 production | 4 | topic-director（原创入口，可跳过）、story-bible、episode-designer、script-writer |
| 质检环（独立技能） | 3 | script-scorer（judge）、compliance-guard（judge）、revision-master（production） |
| 可选 tool | 1 | delivery-tool |

## 部门划分（虚拟编组）

仅用于导航与 orchestration 分 phase，不影响规则加载逻辑。

| dept | 角色 |
|------|------|
| strategy 选题定调部 | topic-director |
| blueprint 剧本蓝图部 | story-bible |
| episode_design 分集设计部 | episode-designer |
| writing 正文创作部 | script-writer |
| quality 质检修复部 | script-scorer, compliance-guard, revision-master |
| delivery 宣发交付部 | delivery-tool |

## v4 → v5 角色映射（能力零丢失）

| v4 角色 | v5 归属 | 能力去向 |
|---------|---------|----------|
| topic-director | 保留 | 不变（modules: market-radar / formula-analysis / tear-down-6d） |
| character-relations | **并入 story-bible** | 人物小传/关系网/轻量世界观 → story_bible 人物层；能力收敛为 character-system |
| series-architect | **并入 story-bible** | 六阶段/主支线/反转位/伏笔总表 → story_bible 结构层；拆分为 series-structure / series-emotion-curve / reversal-foreshadowing |
| episode-designer | 保留 | 输入从三产物改为 story_bible |
| script-writer | 保留 | 输入从 series_outline+character_bible 改为 story_bible |
| revision-master（剧本修订官） | 保留，更名剧本修复官 | 移入质检环；输出后强制复评 |
| script-scorer | 保留 | 独立技能化；输入改为「修复稿优先」any_of，修掉 polished_script 无人消费的断链 |
| compliance-guard | 保留 | 独立技能化；与评分并行；输入同上 |
| delivery-tool | 保留 | 输入改为 story_bible + 最新剧本；前置门禁规则化 |

## Modules（24 个活动模块 + 3 个兼容入口）

| 角色 | modules |
|------|---------|
| topic-director | concept-development, market-radar, formula-analysis, tear-down-6d |
| story-bible | character-system, series-structure, series-emotion-curve, conflict-escalation, reversal-foreshadowing, adaptation-originality |
| episode-designer | episode-card, episode-emotion-nodes, hook-system, conflict-escalation, reversal-foreshadowing, payment-checkpoint |
| script-writer | scene-writing, continuity-snapshot |
| revision-master | dialogue-polish, format-fix, word-count-governance |
| delivery-tool | storyboard-9col, visual-anchor, marketing-copy, delivery-check, story-to-game |

模块正文：`modules/*.md`；机器目录与兼容替代关系：`modules/catalog.yaml`。

## 产物依赖（Artifact DAG）

```
[project_brief]（原创通道）─┐
                           ├→ story_bible
[external_story]（改编通道）┘     ↓
                            narrative_plan
                                 ↓
                            episode_scripts（分批）
                                 ↓ 质检环
                  quality_report + compliance_report（并行，修复稿优先）
                                 ↓ 低于 B 级 / P1
                            polished_script → 复评
                                 ↓ 通过
                          [production_package]（可选）
```

各边定义在对应 `role.yaml` 的 `input_contract` / `output_contract`；`required_artifacts_any_of` 表示按序取第一个存在的产物。

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 人物与全剧结构合并为一份 story_bible | 人物弧光与情节架构强耦合，分开生成易脱节；对齐商业产品「剧本摘要」心智 |
| 双通道共用 story-bible.v1 | 避免双管线维护；改编只是输入不同 |
| 评分/合规/修复独立成环 | 可在任意时点调用（含外部剧本评测）；修复稿强制复评，闭环可收敛 |
| 评分对象「修复稿优先」any_of | 修掉 v4 断链（polished_script 无下游消费） |
| script-writer 分批 `episode_range` | 控制 token；LR-008 逐集上下文 |
| 数值不进 SKILL 正文 | 统一引用 `script-format.yaml` / `quality-scoring.yaml` |
| 进化统一走 drama-intake 四轨道 | 评分官提案、灵感、外部摄入、新模式一个入口，可审计 |

## 体系沿革

| 版本 | 角色数 | 说明 |
|------|--------|------|
| v3.x | 12（8 core + 4 composite） | 部门制雏形，规则三层 SSOT |
| v4.0 | 9（6 生产 + 2 裁判 + 1 工具） | composite 能力收敛为 modules |
| v5.0 | 8（4 主链 + 3 质检 + 1 工具） | 主链收缩、双通道、质检环、进化闭环 |

## 扩展指南

- **新增主链角色**：改 `registry.yaml`、新建 `roles/<slug>/`、补 `stage-playbook.yaml` 条目、更新 orchestration
- **新增题材**：`foundation/rules/genres/<code>.yaml` + 更新 `theme-templates.md`
- **新增 LR**：经 `@drama-intake` 轨道一 → `foundation/rules/learned-rules.yaml`
- 改完运行 `python build/validate_skills.py`

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

## 角色边界

| 角色 | 独占决策 |
|------|----------|
| topic-director | 项目是否值得做、面向谁、以什么差异化立项 |
| story-bible | 人物、世界规则和全剧结构的统一蓝图 |
| episode-designer | 如何把蓝图拆成可直接写作的逐集卡 |
| script-writer | 如何把分集卡转成可拍摄正文 |
| script-scorer | 剧本质量与连续性是否达标 |
| compliance-guard | 内容能否进入制作与发行 |
| revision-master | 在不改变已确认蓝图的前提下修复文本 |
| delivery-tool | 终稿如何转成制作、预算、上架与宣发物料 |

世界观、对白、分镜、预算和平台上架均有独立模块，但不单设角色：它们没有独占审批产物，拆角色只会增加同步成本。

## Modules（30 个活动模块）

| 角色 | modules |
|------|---------|
| topic-director | concept-development, market-radar, formula-analysis, tear-down-6d |
| story-bible | character-system, world-rules, series-structure, series-emotion-curve, conflict-escalation, reversal-foreshadowing, adaptation-originality |
| episode-designer | episode-card, episode-emotion-nodes, hook-system, conflict-escalation, reversal-foreshadowing, payment-checkpoint |
| script-writer | scene-writing, dialogue-craft, continuity-snapshot, production-feasibility |
| script-scorer | continuity-audit |
| revision-master | dialogue-polish, format-fix, word-count-governance |
| delivery-tool | storyboard-9col, visual-anchor, marketing-copy, delivery-check, story-to-game, budget-estimator, platform-ops-checklist |

模块正文：`modules/*.md`；机器目录与挂载关系：`modules/catalog.yaml`。

## 产物依赖（Artifact DAG）

```
[project_brief]（原创通道）─┐
                           ├→ story_bible
[external_story]（改编通道）┘     ↓
                            narrative_plan
                                 ↓
                            episode_scripts（分批）
                                 ↓ 质检环
                  quality_report + compliance_report（并行，读取 latest_script）
                                 ↓ 低于 B 级 / P1
                            polished_script → 复评
                                 ↓ 通过
                          [production_package]（可选）
```

各边定义在对应 `role.yaml` 的 `input_contract` / `output_contract`；当前有效剧本统一由 `latest_script` 虚拟产物解析。

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 人物与全剧结构合并为一份 story_bible | 人物弧光与情节架构强耦合，分开生成易脱节；对齐商业产品「剧本摘要」心智 |
| 双通道共用 story-bible.v1 | 避免双管线维护；改编只是输入不同 |
| 评分/合规/修复独立成环 | 可在任意时点调用（含外部剧本评测）；修复稿强制复评，闭环可收敛 |
| 当前剧本统一为 latest_script | 角色不再各自维护剧本版本优先级 |
| script-writer 分批 `episode_range` | 控制 token；LR-008 逐集上下文 |
| 数值不进 SKILL 正文 | 统一引用 `script-format.yaml` / `quality-scoring.yaml` |
| 进化统一走 drama-intake 四轨道 | 评分官提案、灵感、外部摄入、新模式一个入口，可审计 |

## 扩展指南

- **新增主链角色**：改 `registry.yaml`、新建 `roles/<slug>/`、补 `stage-playbook.yaml` 条目、更新 orchestration
- **新增题材**：扩展 `foundation/theme-matrix.yaml`，继续由 `genres/matrix.yaml` 统一解析
- **新增 LR**：经 `@drama-intake` 轨道一 → `foundation/rules/learned-rules.yaml`
- 改完运行 `python build/validate_skills.py`

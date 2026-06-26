# Drama Skills — AI 短剧创作技能库 v3.1

> **12 角色 · Git SSOT · 四 Scope 规则 · 双轨编排**

本仓库是技能体系的唯一真相源（SSOT）。所有可执行规则在 `foundation/rules/`，角色契约在 `roles/*/role.yaml`，全局索引在 `registry.yaml`。

## 目录结构

```
drama-skills/
├── registry.yaml                 # 12 角色 + 部门 + 工具 + 快速通道
├── foundation/
│   ├── constraints/              # 数值常量（字数/格式/评分阈值）
│   ├── theme-matrix.yaml         # 四轴 9^4 + 69 风味标签 + 32 创新组合
│   ├── methodology/              # 方法论长文
│   └── rules/                    # 规则条目 YAML（global / genre / stage / compliance）
│       └── genres/               # 规则模板（8 预设 + hybrid）的 genre 规则
├── roles/<slug>/                 # 每角色：role.yaml + SKILL.md [+ tasks/]
├── modules/                      # 复合角色能力块（Markdown）
├── orchestration/                # fast-track / expert-track 流程
├── knowledge/                    # 参考长文（规则 body 可引用）
├── inspirations/                 # 创意素材库
├── drama-master/                 # 总入口 @drama-master
├── drama-intake/                 # 外部摄入 @drama-intake
└── build/                        # 仓库维护脚本
```

## 安装（Cursor）

将 `drama-skills/` 复制到项目的 `.cursor/skills/`，或将各 `roles/*/SKILL.md` 按需链接。总入口：

```
.cursor/skills/drama-master/
```

触发：`@drama-master` 或 `@drama-plot-architect` 等。

## 角色一览（12）

| agent_id | 中文 | 类型 | 默认产物 |
|----------|------|------|----------|
| drama.topic-planner | 选题策划官 | core | project_brief |
| drama.market-analyst | 市场分析师 | composite | market_report |
| drama.world-architect | 世界架构师 | core | world_setting |
| drama.character-designer | 人设设计师 | core | character_bible |
| drama.plot-architect | 情节架构师 | core | series_outline |
| drama.narrative-engineer | 叙事工程师 | composite | narrative_plan |
| drama.script-writer | 剧本执笔师 | core | episode_scripts |
| drama.script-reviewer | 审稿官 | core | review_report |
| drama.quality-reporter | 质量报告官 | core | quality_report |
| drama.polish-master | 精修大师 | composite | polished_script |
| drama.production-pack | 制作发行师 | composite | production_package |
| drama.compliance-guard | 合规守卫 | core | compliance_report |

## 双轨流程

- **快速通道**（8 步）：见 `orchestration/fast-track.yaml`
- **专家通道**（12 角色分阶段）：见 `orchestration/expert-track.yaml`

## 改规则 / 加角色

| 操作 | 改哪里 |
|------|--------|
| 增删改规则条目 | `foundation/rules/*.yaml` |
| 改字数/格式阈值 | `foundation/constraints/script-format.yaml` |
| 改角色 I/O | `roles/<slug>/role.yaml` |
| 注册新角色 | `registry.yaml` + 新建 `roles/<slug>/` |
| 改流程顺序 | `orchestration/*.yaml` |
| 四轴矩阵 / 题材映射 | `foundation/theme-matrix.yaml` |
| 规则模板量化参数 | `knowledge/theme-templates.md` + `foundation/rules/genres/` |

## 文档索引

| 文件 | 用途 |
|------|------|
| `knowledge/knowledge-sections.md` | Section 名 ↔ 角色映射 |
| `knowledge/tier3-stage-rules.md` | 各角色阶段 playbook 参考长文 |
| `knowledge/output-schemas.md` | 产物 JSON 字段参考 |
| `INTAKE_PROTOCOL.md` | 外部内容摄入协议 |
| `EVOLUTION_LOG.md` | 进化记录 |
| `ROLE-DESIGN-ANALYSIS.md` | 12 角色设计说明 |

---

*Drama Skills v3.1 · Git SSOT · 山音方法论 + 短剧行业规则*

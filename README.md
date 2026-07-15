# Drama Skills — AI 短剧创作技能库 v5.0

> **4 主链生产角色 · 3 质检环独立技能 · 1 可选交付工具 · 双通道 · Git SSOT**

本仓库是技能体系的唯一真相源（SSOT）。数值约束在 `foundation/constraints/`，原子规则在
`foundation/rules/`，执行流程在 `modules/`，角色契约在 `roles/*/role.yaml`。

## 目录结构

```
drama-skills/
├── registry.yaml                 # 角色 + 部门 + 主链 + 工具索引
├── foundation/
│   ├── constraints/              # 数值常量（含 config_tier 分级：git_ssot / seed_default）
│   ├── theme-matrix.yaml         # 四轴 9^4 + 69 风味标签 + 32 创新组合
│   ├── methodology/              # 方法论长文
│   └── rules/                    # 规则条目 YAML，8 个主题 global 文件 + stage + compliance
│       └── genres/matrix.yaml    # 四轴合成后的题材规则入口
├── roles/<slug>/                 # 每角色：role.yaml + SKILL.md [+ tasks/]
├── modules/                      # 能力块（输入/规则引用/输出/步骤/失败条件/自检）
│   └── catalog.yaml             # 模块领域、角色挂载与条件加载目录
├── manifest/                     # Bundle清单与后台覆盖白名单
├── workbench/                    # 工作台字段、阶段、面板与API契约
├── schemas/                      # 项目、流程、后台与全部产物JSON Schema
├── orchestration/                # original-track / story-adapt-track 双通道
├── runtime/                      # 流程状态机参考实现
├── quality/                      # 确定性质量回归用例
├── knowledge/                    # 参考长文（按消费场景分目录）
│   ├── craft/                    #   创作方法论（山音编剧/题材/阶段/LR详解）
│   ├── market/                   #   市场数据（时效性，后台配置候选）
│   ├── quality/                  #   质检标准（S级/预设/合规/原创性）
│   ├── production/               #   制作宣发（导演方法论/互动改编）
│   ├── system/                   #   系统方法论（流程控制）
│   ├── knowledge-sections.md     #   Section↔角色索引（后端固定路径解析，勿移动）
│   └── output-schemas.md         #   产物 schema 索引
├── inspirations/                 # 创意素材库（进化轨道二/四写入）
├── drama-master/                 # 创作总入口 @drama-master
├── drama-intake/                 # 技能进化入口 @drama-intake
└── build/                        # 解析器、导出器、校验脚本、fixtures与单元测试
```

机器可读治理入口：`manifest/drama-skills.manifest.yaml`；
后台覆盖边界：`manifest/config-policy.yaml`。

## 独立仓库（demo_guo）

本目录在 ScriptForge 内保留副本；**独立技能仓**推送到：

- 仓库：`https://github.com/mymubit/demo_guo`
- 分支：`drama-skills`
- 内容：本目录全部文件（仓库根即技能根，含 `registry.yaml`）

在 ScriptForge 根目录同步推送：

```bash
chmod +x drama-skills/scripts/publish_to_demo_guo.sh
./drama-skills/scripts/publish_to_demo_guo.sh
```

**前置**：GitHub 上已创建空仓库 `demo_guo`（不要勾选「Initialize with README」）。

ScriptForge 引用独立仓时设置环境变量：

```bash
export DRAMA_SKILLS_ROOT=/path/to/demo_guo   # clone 后指向仓库根
python manage.py sync_drama_from_git
```

## 安装（Cursor）

将 `drama-skills/` 复制到项目的 `.cursor/skills/`，或将各 `roles/*/SKILL.md` 按需链接。总入口：

```
.cursor/skills/drama-master/
```

触发：`@drama-master` 或 `@drama-story-bible` 等。

## 角色一览（4 + 3 + 1）

| agent_id | 中文 | 类型 | 默认产物 |
|----------|------|------|----------|
| drama.topic-director | 选题定调官 | production（主链·原创入口） | project_brief |
| drama.story-bible | 剧本蓝图官 | production（主链·双模式） | story_bible |
| drama.episode-designer | 分集设计官 | production（主链） | narrative_plan |
| drama.script-writer | 剧本正文官 | production（主链·分批） | episode_scripts |
| drama.script-scorer | 剧本评分官 | judge（质检环·独立技能） | quality_report |
| drama.compliance-guard | 合规审查官 | judge（质检环·独立技能） | compliance_report |
| drama.revision-master | 剧本修复官 | production（质检环·独立技能） | polished_script |
| drama.delivery-tool | 宣发交付工具 | tool（可选） | production_package |

## 双通道流程

| 通道 | 入口 | 链路 |
|------|------|------|
| **原创创作**（`orchestration/original-track.yaml`） | 一个想法 / 四轴选题 | 选题 → 蓝图 → 分集 → 正文 + 质检环 |
| **故事改编**（`orchestration/story-adapt-track.yaml`） | 用户自带故事/小说/大纲 | 蓝图（改编模式）→ 分集 → 正文 + 质检环 |

**质检环**（每批正文完成后）：评分官 + 合规官并行 → 低于 B 级（75）或有 P1 → 修复官 → 复评通过才可继续。

## 技能进化

进化入口 `@drama-intake`，四条轨道（定义见 `drama-intake/SKILL.md`）：

| 轨道 | 用途 | 写入 |
|------|------|------|
| 一 · 规则进化 | 方法论/阈值/LR 提案（含评分官自动提案） | `foundation/rules/*.yaml` |
| 二 · 灵感归档 | 钩子/反转/对白/结构案例 | `inspirations/` |
| 三 · 市场知识 | 行业数据/平台趋势 | `knowledge/market/market-insights.md` |
| 四 · 新模式发现 | 未覆盖的新规律（3+ 案例验证后升格） | `inspirations/new-patterns.md` |

## 改规则 / 加角色

| 操作 | 改哪里 |
|------|--------|
| 增删改规则条目 | `foundation/rules/*.yaml` |
| 改数值、枚举、阈值或产物结构 | `foundation/constraints/*.yaml` |
| 改能力执行步骤 | `modules/*.md`，并登记 `modules/catalog.yaml` |
| 改角色 I/O | `roles/<slug>/role.yaml` |
| 注册新角色 | `registry.yaml` + 新建 `roles/<slug>/` + `stage-playbook.yaml` 条目 |
| 改流程顺序 | `orchestration/*.yaml` |
| 四轴矩阵 / 题材映射 | `foundation/theme-matrix.yaml` |
| 规则模板量化参数 | `foundation/theme-matrix.yaml` + `foundation/rules/genres/matrix.yaml` |

改完运行一致性校验：`python build/validate_skills.py`

工作台或后台配置变化还必须运行：

```bash
python build/validate_workbench.py
python build/validate_artifacts.py
python build/validate_config.py
python build/validate_workflow.py
python build/validate_quality_cases.py
```

## 工作台与后台配置边界

- 项目设置：题材四轴、风味标签、集数、平台、制作复杂度目标、评分预设、批次和交付选项，见 `workbench/workbench.yaml`。
- 运营后台：只能覆盖 `manifest/config-policy.yaml#overlay_files` 白名单中的 seed defaults。
- Git 硬规则：角色组合、原子规则、编排拓扑、产物契约、题材枚举和合规红线禁止后台覆盖。
- 每次后台修改必须记录版本、操作人、时间和原因，并保留可回滚历史。

前端通过 `python build/export_workbench_schema.py` 导出表单定义，并按
`workbench/api-contract.yaml` 接入 ScriptForge。当前独立技能仓不包含网站前后端源码。

## 底层知识分层

依赖方向必须保持单向：

```text
knowledge（原因、案例、行业背景）
  → foundation/constraints（数值与结构 SSOT）
  → foundation/rules（可注入原子规则）
  → modules（执行流程与字段映射）
  → roles / orchestration（上层挂载与编排）
```

- `knowledge/` 不声明运行时 SSOT，不整篇注入代替规则。
- 原子规则通过 `source_ref` 追溯知识来源，不引用 module 为 SSOT。
- module 不重复规则全文和数值，只引用 `rule_key` / constraint 路径。
- 尚未进入角色设计的基础模块使用 `catalog.yaml` 的 `foundation` 状态，不视为孤儿。

## 文档索引

| 文件 | 用途 |
|------|------|
| `knowledge/knowledge-sections.md` | Section 名 ↔ 角色映射 |
| `knowledge/craft/tier3-stage-rules.md` | 各角色阶段 playbook 参考长文 |
| `knowledge/output-schemas.md` | 产物 JSON 字段参考（含 story-bible.v1） |
| `INTAKE_PROTOCOL.md` | 外部内容摄入协议 |
| `EVOLUTION_LOG.md` | 进化记录 |
| `ROLE-DESIGN-ANALYSIS.md` | 角色设计说明（v5） |

---

*Drama Skills v5.0 · Git SSOT · 山音方法论 + 短剧行业规则*

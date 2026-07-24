# Drama Skills — AI 短剧创作技能库 v5.2

> **4 主链生产角色 · 3 质检环独立技能 · 1 可选交付工具 · 双通道 · Git SSOT**

本仓库是技能体系的唯一真相源（SSOT）。**铁律叙述**在 `foundation/rules/`，**硬指标**在
`foundation/constraints/`，**可调预设**在 `foundation/presets/`，执行流程在 `modules/`，角色契约在 `roles/*/role.yaml`。

## 五层能力模型（导航）

与总纲 `docs/superpowers/specs/2026-07-20-skills-optimization-program-design.md` 对齐：

| 层 | 放什么 | 本仓目录 |
|----|--------|----------|
| L5 观测 | 诊断/Manifest（运行时，不在本仓） | — |
| L4 装配策略 | `role.yaml` 的 module/knowledge/rule_policy | `roles/*/role.yaml` |
| L3 技能编排 | SKILL、fewshot、anti、轨道 | `roles/`、`orchestration/` |
| L2 模块 | 可条件启停步骤 | `modules/` |
| L1 规则与预设 | 铁律 + 硬指标 + 可调预设；长文知识可选注入 | `foundation/rules/`、`foundation/constraints/`、`foundation/presets/`、`knowledge/` |
| 配置子树 | 契约与 schema（不进 prompt 全文） | `contracts/`、`schemas/`、`workbench/`、`manifest/` |
| 工具 | 校验/生成 | `tools/`（`python tools/validators/validate_all.py`） |

**≤2 跳定位「钩子密度数值」**：`foundation/rules/INDEX.md` → `05-hooks-payoff.yaml`（叙述）→ `foundation/constraints/commercial-formulas.yaml#first_episode_hook_count`（数值 SSOT）。

## 目录结构

```
drama-skills/
├── contracts/                    # 产物与参数机器契约（SSOT）
│   ├── artifacts.yaml            #   产物键、schema、producer、分片
│   └── parameters.yaml           #   可传递参数类型与角色引用
├── registry.yaml                 # 角色 + 部门 + 主链 + 工具索引
├── foundation/
│   ├── constraints/              # 硬指标 / 方法论 SSOT（含 git_ssot）
│   ├── presets/                  # 可调预设（seed_default，后台可 overlay）
│   ├── theme-matrix.yaml         # 频道 + 四轴 9^4 + 主角结构 + 72 风味标签 + 34 创新组合
│   └── rules/                    # 规则条目 YAML（铁律；见 INDEX.md）
│       └── genres/               # matrix.yaml（四轴合成）
├── roles/<slug>/                 # 每角色：role.yaml + SKILL.md [+ tasks/]
├── modules/                      # 能力块（输入/规则引用/输出/步骤/失败条件/自检）
│   └── catalog.yaml             # 模块领域、角色挂载与条件加载目录
├── manifest/                     # Bundle清单与后台覆盖白名单
├── workbench/                    # 工作台字段、阶段、面板与API契约
├── schemas/                      # 项目、流程、后台与全部产物JSON Schema
│   └── generated/                #   由 contracts/parameters.yaml 生成的参数定义（禁止手改）
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
├── inspirations/                 # 创意素材库（轨道 B；正文 SSOT = inspirations.md）
├── tools/                        # 🛠️ 工具链（validators / generators / optimizers / lib）
│   ├── validators/               #   校验（含 validate_all）
│   ├── generators/               #   契约生成与导出
│   ├── optimizers/               #   低频优化脚本
│   ├── lib/                      #   公共库
│   ├── fixtures/                 #   校验样例
│   └── tests/                    #   工具链单测
├── drama-master/                 # 创作总入口 @drama-master
├── drama-intake/                 # 技能进化入口 @drama-intake
└── eval/tools/                   # 角色 LLM 评测
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

**质检环**（每批正文完成后）：默认先评分，达 B 档再合规（B′；可配置并行）→ 未达标 → 修复官 → 复评通过才可继续。

## 技能进化

进化入口 @drama-intake，**两条轨道**（定义见 drama-intake/SKILL.md v5.1）：

| 轨道 | 用途 | 写入 |
|------|------|------|
| A · 规则升级 | 方法论/频率/LR 提案（含评分官自动提案、模式升格） | oundation/rules/*.yaml |
| B · 素材沉淀 | 钩子/反转/对白/结构/待验证模式；市场数据 | inspirations/inspirations.md；knowledge/market/market-insights.md |

## 改规则 / 加角色

| 操作 | 改哪里 |
|------|--------|
| 增删改规则条目 | `foundation/rules/*.yaml` |
| 改可传递参数类型/枚举/默认/边界 | `contracts/parameters.yaml`，再运行 `python tools/generators/generate_parameter_schemas.py` |
| 改数值、枚举、阈值（非参数契约） | `foundation/constraints/*.yaml` |
| 改产物结构 | `contracts/artifacts.yaml` + `schemas/artifacts/<key>/1.schema.json` |
| 改能力执行步骤 | `modules/*.md`，并登记 `modules/catalog.yaml` |
| 改角色 I/O | `roles/<slug>/role.yaml` |
| 注册新角色 | `registry.yaml` + 新建 `roles/<slug>/` + `stage-playbook.yaml` 条目 |
| 改流程顺序 | `orchestration/*.yaml` |
| 四轴矩阵 / 题材映射 | `foundation/theme-matrix.yaml` |
| 规则模板量化参数 | `foundation/theme-matrix.yaml` + `foundation/rules/genres/matrix.yaml` |

改完运行一致性校验：`python tools/validators/validate_skills.py`

参数契约变更后须重新生成并校验 Schema：

```bash
python tools/generators/generate_parameter_schemas.py
python tools/generators/generate_parameter_schemas.py --check
```

工作台或后台配置变化还必须运行：

```bash
python tools/validators/validate_all.py
```

## 工作台与后台配置边界

- 项目设置：题材四轴、风味标签、集数、平台、制作复杂度目标、评分预设、批次和交付选项，见 `workbench/workbench.yaml`。
- 运营后台：只能覆盖 `manifest/config-policy.yaml#overlay_files` 白名单中的 seed defaults。
- Git 硬规则：角色组合、原子规则、编排拓扑、产物契约、题材枚举和合规红线禁止后台覆盖。
- 每次后台修改必须记录版本、操作人、时间和原因，并保留可回滚历史。

前端通过 `python tools/generators/export_workbench_schema.py` 导出表单定义，并按
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
| `knowledge/output-schemas.md` | 产物 JSON 字段参考（含 story_bible v1） |
| `INTAKE_PROTOCOL.md` | 外部内容摄入协议 |
| `EVOLUTION_LOG.md` | 进化记录 |
| `ROLE-DESIGN-ANALYSIS.md` | 角色设计说明（v5） |

---

*Drama Skills v5.0 · Git SSOT · 山音方法论 + 短剧行业规则*

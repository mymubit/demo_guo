# Drama Skills v5.1 底层技能治理方案（完整版）

> 本文档是技能库深度重组的最终方案与执行记录：三层架构定位、底层文件全量清点、
> 未使用技能处置、Git 与后台配置的划分、以及商业化网站的分阶段实施计划。
> 执行状态标注：✅ 本次已完成（技能库层）/ 🔜 待后端实施。

---

## 一、三层消费链：每个文件到底被谁用（评估结论）

商业网站运行时的实际消费链（依据 `backend/apps/drama/skills_registry.py` 与 `seed_drama_skills.py`）：

| 技能库文件 | 网站运行时如何消费 | Cursor 技能场景如何消费 |
|-----------|------------------|----------------------|
| `registry.yaml` | 角色/部门/主链索引，seed 进 `AgentDefinition` | 索引 |
| `roles/*/role.yaml` | 输入输出契约、rule_policy | 契约 |
| `roles/*/SKILL.md` **正文** | **直接成为角色 system prompt**（`build_system_prompt`） | 触发入口 |
| `foundation/rules/*.yaml` 逐条 items | 按 scope/section **注入用户 prompt**（Tier1-4 规则块） | 规则参考 |
| `foundation/constraints/*.yaml` | 字数校验、评分维度、流式分片、LLM 参数 seed | 数值参考 |
| `knowledge/knowledge-sections.md` | **后端按固定路径解析**角色↔Section 表（不可移动） | 索引 |
| `knowledge/` 其余长文 | ❌ **不进入运行时**（知识注入走 DB `AgentKnowledgeItem`） | SKILL references 延伸阅读 |
| `modules/*.md` | ❌ **不进入运行时**（仅模块名列表进 ui_schema 元数据） | 能力块正文 |
| `orchestration/*.yaml` | 阶段计划/进度展示 | 流程参考 |

**由此得出的两个关键评估结论：**

1. **modules 与 knowledge 曾是「注册了但没被真正使用」的两层**：模块只有 3 行存根、
   知识长文不进 prompt——网站产出质量实际只依赖 SKILL 正文 + 规则条目。
   → 处置：模块全量充实为可执行操作指南（作为 Cursor 场景正文 + 后续可 seed 进
   `AgentKnowledgeItem` 的素材源）；知识长文全部挂接消费角色。✅
2. **规则条目是 prompt 的实际载体**，其中大量条目只有一行「SSOT: knowledge/xxx.md」
   指针——运行时读不到指针背后的内容，等于空规则。
   → 处置：合并碎片文件、把可执行内容内联进 body、指针降级为「长文参考」注释。✅

---

## 二、底层技能文件全量清点与处置（54 个文件）

### 2.1 modules/（16 个 → 全量充实，✅ 完成）

原状：14/16 个模块仅 3 行存根（空心技能）。现每个模块统一为
「目标 → 执行步骤 → 量化标准 → 自检清单」结构（30-60 行），并标注挂载角色与数值 SSOT：

| 模块 | 挂载角色 | 充实后核心内容 |
|------|---------|---------------|
| psychology-immersion | story-bible | 痛点锚定 5 步法、代入感公式、反应合理性校验 |
| emotion-blueprint | story-bible / episode-designer | QDN 模型、全剧/单集双层执行步骤、EV/ET/TP、双轨节奏熔断线 |
| conflict-escalation | story-bible / episode-designer | 四类冲突表、升级协议、对峙五要素 |
| reversal-system | story-bible / episode-designer | 五类反转铺垫要求表、逆向设计法、密度布局 |
| hook-system | episode-designer | 四级钩子表、黄金 30 秒、集末钩子四写法 |
| market-radar | topic-director | 热点定位→竞品→空白点→梦境指标→平台适配 5 步 |
| formula-analysis | topic-director | 五项量化公式表（钩子密度≥7 等，作为数值 SSOT） |
| tear-down-6d | topic-director | 六维拉片表、模板提炼、进化轨道路由 |
| dialogue-polish | revision-master | 五类台词问题检测-修复表、朗读测试 |
| format-fix | revision-master | 格式三件套、五类违规修复表、FER 计算 |
| word-count-governance | revision-master | 四类症状分级处理策略表 |
| storyboard-9col | revision-master | 九列表规范、节奏基准、镜头对设计 |
| visual-anchor | delivery-tool | 视觉锚点提取、Prompt 结构模板、IP 肖像权自检 |
| marketing-copy | delivery-tool | 平台差异化表、五类交付物、0-3-8-15 投流结构 |
| delivery-check | delivery-tool | 六项门禁表（含依据 SSOT）、缺口清单机制 |
| story-to-game | delivery-tool | 三类分支配比、九步压缩流程、死路校验 |

### 2.2 foundation/rules/（17 个 → 12 个，✅ 完成）

后端按「根目录 *.yaml + genres/*.yaml」全量读取、按条目 section 过滤，
因此**合并文件对运行时透明**（rule_key/section 全部保留不变）：

| 处置 | 明细 |
|------|------|
| 合并 | `dialogue-voice` + `ai-tone-forbidden` → **`dialogue-rules.yaml`** |
| 合并 | `writing-requirements` + `writing-prohibitions` → **`writing-rules.yaml`** |
| 合并 | `conflict-escalation` + `foreshadowing-rules` + `payment-checkpoint` → **`plotting-rules.yaml`**（情节工程） |
| 重命名+扩充 | `character-logic` → **`character-rules.yaml`**（新增密度/弧光硬约束条目） |
| 强化 | `genre-profile.yaml` 空话 fallback → 补充可执行摘要 + 未命中题材默认参数条目 |
| 保留 | `philosophy` / `narrative-craft` / `rhythm-rules` / `scoring-core` / `learned-rules` / `stage-playbook` / `compliance-core` / `genres/` |

条目 body 治理原则（✅ 已执行）：可执行内容（阈值/清单/公式）必须内联在 body 中；
knowledge 长文只作「长文参考」注释，不再充当规则本体。

### 2.3 knowledge/（20 个 → 按消费场景分 5 个子目录，✅ 完成）

| 目录 | 文件 | 消费角色（已挂接进 SKILL references） |
|------|------|-----------------------------------|
| `craft/` 创作方法论 | shanyin-screenwriting-methodology、shanyin-feature-format、shanyin-series-format、tier2-genre-rules、tier3-stage-rules、theme-templates、learned-rules（LR 详解） | story-bible / episode-designer / script-writer |
| `market/` 市场数据 | douyin-formulas、industry-benchmarks、market-insights | topic-director（**后台配置候选**，见第三节） |
| `quality/` 质检标准 | s-class-standards、scoring-presets、tier4-compliance、originality-rules | script-scorer / compliance-guard / story-bible（改编自检） |
| `production/` 制作宣发 | shanyin-director-methodology、shanyin-director-styles、story-to-game | revision-master（九列分镜）/ delivery-tool |
| `system/` 系统方法论 | storyforge-runtime-methodology | drama-master（流程控制参考） |
| 根目录（后端硬编码路径，不可移动） | knowledge-sections.md、output-schemas.md | 后端解析 / schema 索引 |

### 2.4 未使用/空心技能清单与处置结论

| 项 | 原状态 | 评估 | 处置 |
|----|--------|------|------|
| 14 个 3 行模块存根 | 注册了但无实质内容 | 空心技能（最严重） | ✅ 全量充实 |
| `knowledge/story-to-game.md` vs `modules/story-to-game.md` | 双份重复 | 保留：长文=方法论、模块=操作指南，已互相链接 | ✅ 分工明确化 |
| `learned-rules.md` vs `learned-rules.yaml` | 双 SSOT 混乱 | YAML=可执行摘要（注入用），MD=详解长文 | ✅ 分工明确化 |
| shanyin 5 篇长文 | 完全无引用（孤儿） | 有价值：横截面/McKee/九列分镜的源头方法论 | ✅ 挂接对应角色 |
| industry-benchmarks / market-insights / scoring-presets / s-class-standards | 完全无引用（孤儿） | 有价值 | ✅ 挂接 topic-director / script-scorer |
| storyforge-runtime-methodology | 孤儿 + 引用旧角色 | 对后端流程设计有价值 | ✅ 更新为 v5 角色并挂接 drama-master |
| `originality-rules.md` | 孤儿 | 改编通道刚好需要 | ✅ 挂接 story-bible 改编模式 + compliance-guard |
| artifact-chunk-map 中 `world_setting` / `review_report` / `market_report` 键 | 无生产者的死键 | 死配置 | ✅ 已删除（v5.0） |
| `emotion_curve` / `hook_plan` 输入键 | 无生产者 | 死契约 | ✅ 已删除（v5.0） |
| `memory-checkpoint` task 声明 | 无对应文件 | 断链 | ✅ 已删除（v5.0） |

**防复发机制（✅）**：`build/validate_skills.py` 新增 4 项检查——knowledge 孤儿检测、
模块孤儿检测、全库相对路径引用有效性、角色↔Section 映射存在性。今后任何文件变成孤儿或断链，校验直接报错。

---

## 三、Git SSOT 与后台管理配置的划分（商业化评估结论）

划分标准：**方法论与契约进 Git（需评审、可回滚、跨环境一致）；
运营参数与时效数据进后台（运营可调、即时生效、可灰度）。**

已在各 constraints 文件头部标注 `config_tier`：

| 配置项 | 归属 | 理由与现状 |
|--------|------|-----------|
| 角色契约 / 规则条目 / 模块 / schema / 编排 | **git_ssot** | 创作方法论=代码，改动必须走 PR 评审 + 校验器 |
| LLM 参数（temperature/max_tokens/模型路由） | **后台**（已有 `/admin/drama-models` + `AgentLlmRouteConfig`） | agent-runtime.yaml 降级为 seed 默认值 ✅ 已标注 |
| 等级阈值 / 通过线 / 返修轮数上限 / 熔断参数 | **后台可覆盖**（`system_config`），quality-scoring.yaml 提供默认 | 运营需要按套餐/活动调整质检严格度 ✅ 已标注 |
| 字数区间 / 台词占比 / 场景数 | **后台可覆盖**，script-format.yaml 提供默认 | 不同平台/会员档位产品参数不同 ✅ 已标注 |
| 剧本格式 pattern / 格式禁止项 | **git_ssot** | 行业格式规范，非运营参数 ✅ 已标注 |
| 市场数据（knowledge/market/ 三篇） | **后台**（时效数据，建议迁 `AgentKnowledgeItem` 或运营知识表） | Git 中保留为初始 seed；标注「冲突时以后台最新数据为准」✅ |
| 题材矩阵四轴/标签枚举 | **git_ssot**（含校验脚本） | 结构性枚举，前后端契约 |
| featured_combos 创新组合 / 预设卡片 | **后台候选**（运营内容） | 阶段二迁移，Git 保留 seed |
| artifact-chunk-map | **git_ssot** | 纯工程配置，随代码走 |
| 进化产物（LR 新增、new-patterns） | **Git（经 PR）** | 进化必须可审计，drama-intake 轨道一已定义提案→确认→写入流程 |

### 后台配置中心实施设计（🔜 阶段二，复用现有 `apps/system_config`）

1. **配置键规划**（`drama.quality.*` / `drama.format.*` 命名空间）：
   `drama.quality.grade_thresholds`、`drama.quality.pass_threshold`、`drama.quality.max_rewrites`、
   `drama.quality.fuse_rules`、`drama.format.episode_word_count`、`drama.format.dialogue_ratio_min`、
   `drama.format.scenes_per_episode`
2. **读取链改造**：`skills_registry.get_quality_grade_thresholds()` 等函数改为
   `get_config(key) → 缺省回落 YAML seed` 的两级读取（Redis/进程缓存 + 写时刷新），
   业务代码入口不变，天然支持灰度回退
3. **管理页**：挂在现有 Admin 下（drama-models 旁新增「创作参数」Tab），管理员权限 + 修改日志
4. **市场知识迁移**：`knowledge/market/*.md` 结构化为知识条目 seed 进 `AgentKnowledgeItem`
   （category=market），运营后台可增改，drama-intake 轨道三的写入目标同步改为该表

---

## 四、本次已完成 vs 后续阶段

### 阶段一（✅ 本 PR，技能库层全部完成）

- v5.0：角色 9→8、双通道编排、质检环断链修复、进化机制统一（前序提交）
- v5.1：16 模块全量充实；rules 17→12 按主题合并、指针降级、弱规则强化；
  knowledge 分 5 目录重组并全量挂接；constraints 配置分级标注；
  校验器新增孤儿/断链/映射 4 项检查；全部校验通过

### 阶段二（🔜 后端适配 + 配置中心，建议合并本 PR 后立即启动）

1. `skills_registry.py`：编排文件名（original-track/story-adapt-track）、`DEPT_TO_DRAMA_STAGE`
   新部门映射、`_fallback_entry_plan` 更新、`SKILL_VERSION` 提升
2. `IndependentAgentService` 支持 `required_artifacts_any_of` 输入装配（修复稿优先）
3. `story_bible` 产物存取（chunk-map 已留 character_bible/series_outline 兼容别名）
4. `system_config` 配置键 + 两级读取 + Admin 管理页（第三节设计）
5. 质检环执行引擎：评分+合规并行触发、低于 B 级自动建议修复、复评闭环
   （补上 GenerationPlan「有壳无芯」的执行逻辑）
6. 测试更新：`test_workspace_api` 角色数断言、新增 any_of 契约与配置覆盖测试

### 阶段三（🔜 前端对齐）

- `WORKFLOW_STAGES`/`agentTerm`/`dramaBatchRoleUi` 等平行副本改为 `/api/drama/roles/` 下发
- 双通道入口 UI（新建项目时选择「从零创作 / 我有故事」）

---

## 五、治理约束（长期有效）

1. 新增角色/模块/知识文件必须过 `python build/validate_skills.py`（孤儿即报错）
2. 规则 body 必须自含可执行内容；knowledge 只能作「长文参考」注释
3. 数值只允许出现在 `foundation/constraints/`（Git seed）或后台配置中，规则/文档引用不复制数值本体（引用处标注 SSOT）
4. 运营参数改动走后台；方法论改动走 PR + EVOLUTION_LOG 记录
5. 技能进化统一走 `@drama-intake` 四轨道，禁止绕过提案流程直接改规则

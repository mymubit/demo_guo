# 知识规则区块索引（Knowledge Sections）

> 来源：ScriptForge `backend/apps/agent/bootstrap/tier1_sections.py`
> 
> 每个创作角色（Agent）依赖特定的知识规则区块（Sections）。本文档定义各区块内容，
> 便于理解每个角色的"必读知识范围"，也是外部内容摄入时的分类依据。

---

## 区块定义

| 区块名 | 中文名 | 内容说明 | 被哪些角色使用 |
|--------|--------|---------|------------|
| `philosophy` | 创作哲学 | 短剧创作的底层理念（情绪驱动、节奏高于一切等） | brief/structure/character/adapt |
| `rhythm_rules` | 节奏规则 | 钩子密度、中段节律、高潮区间规则 | structure/outline/rhythm-designer |
| `episode_structure` | 集段结构 | 四段式（钩子/情境/升级/悬念）+六阶段叙事 | structure/outline/script |
| `episode_emotion_8nodes` | 8节点情绪图 | 每集8个固定时间点的情绪目标值 | structure/script/emotion-architect |
| `foreshadowing_rules` | 伏笔规则 | 伏笔布局时间、密度、揭露规范 | structure/character/outline/insight |
| `scoring` | 评分规范 | 八维评分体系、各维度权重和标准 | review/score/insight |
| `quantitative_constraints` | 量化约束 | 台词字数上限、场景数量、节奏参数 | outline/script |
| `writing_prohibitions` | 写作禁忌 | 禁止的写作方式（AI腔、直接说情绪等） | script/polish/adapt |
| `writing_requirements` | 写作要求 | 必须遵守的创作规范 | script/polish |
| `information_asymmetry_mechanics` | 信息不对称机制 | 观众视角优势、已知/未知信息设计 | script |
| `emotion_externalization_dict` | 情绪外化词典 | 各情绪状态对应的动作/道具/环境外化方式 | script/polish/emotion-architect |
| `ai_tone_forbidden` | AI腔禁用词 | 具体的AI腔表达和修复方式 | script/polish |
| `qdn_emotion_model` | QDN情绪模型 | 质量感×深度×需求满足的情绪量化模型 | outline/script/emotion-architect |
| `format_standard` | 格式规范 | 商业剧本格式（场景头/台词/△标记） | script |
| `hook_effectiveness` | 钩子有效性 | S/A/B/C钩子分级、强度公式、开篇设计 | outline/script/hook-designer/marketing |
| `dialogue_quality` | 对白质量 | 台词自然化标准、潜台词技法 | script/polish |
| `payment_checkpoint_3card` | 三卡付费关卡 | 付费卡点设计的三种核心类型 | outline |

---

## 各角色知识区块映射

### ScriptForge Agents

| Agent | 使用的知识区块 |
|-------|-------------|
| `brief` (立项简报) | philosophy |
| `structure` (结构设定) | philosophy, rhythm_rules, episode_structure, episode_emotion_8nodes, foreshadowing_rules, scoring |
| `character` (人物小传) | philosophy, foreshadowing_rules |
| `outline` (分集大纲) | episode_structure, rhythm_rules, quantitative_constraints, foreshadowing_rules, qdn_emotion_model, hook_effectiveness, payment_checkpoint_3card |
| `script` (剧本正文) | 12个区块（全量） |
| `review` (质量审查) | scoring |
| `polish` (润色) | writing_prohibitions, writing_requirements, ai_tone_forbidden, emotion_externalization_dict, dialogue_quality |
| `score` (评分) | scoring |
| `emotion_architect` | episode_emotion_8nodes, qdn_emotion_model, hook_effectiveness, emotion_externalization_dict |
| `marketing` | hook_effectiveness |

---

## 与 drama-skills/ 角色的对应关系

| 知识区块 | 对应 drama-skills/ 角色 |
|---------|----------------------|
| philosophy | drama-topic-planner (立项哲学) |
| rhythm_rules | drama-rhythm-designer |
| episode_structure | drama-plot-architect |
| episode_emotion_8nodes | drama-emotion-architect |
| foreshadowing_rules | drama-reversal-master（伏笔部分） |
| scoring | drama-quality-reporter |
| quantitative_constraints | drama-formatter + drama-script-writer |
| writing_prohibitions | drama-script-editor + drama-dialogue-expert |
| writing_requirements | drama-script-writer |
| information_asymmetry_mechanics | drama-hook-designer + drama-psychology-architect |
| emotion_externalization_dict | drama-emotion-architect + drama-dialogue-expert |
| ai_tone_forbidden | drama-dialogue-expert |
| qdn_emotion_model | drama-emotion-architect |
| format_standard | drama-formatter |
| hook_effectiveness | drama-hook-designer |
| dialogue_quality | drama-dialogue-expert |
| payment_checkpoint_3card | drama-formula-analyst |

---

## 外部内容摄入时的分类指引

提交外部内容后，摄入器（drama-intake）会根据内容特征，将知识点归类到以上区块，再路由到对应角色文件进行更新。

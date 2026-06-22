# Drama Skills — AI短剧创作技能库 v2.1

> **29 个专业角色 · 8 个职能部门 · 三平台兼容 · 四轨道自我进化**
> 
> 整合三个分支：`ScriptForge`（主库+Tier1规则体系）+ `dramaskill`（节点系统+参考库）+ `dramaskilltrae`（39个专业技能）

---

## 安装说明

| 平台 | 技能文件夹路径 | 使用方式 |
|------|--------------|---------|
| **Cursor** | `.cursor/skills/<技能名>/` | `@技能名` 触发 |
| **Codex** | `.codex/<技能名>/` 或直接引用 | `[角色]` 触发 |
| **Trae** | 项目根目录技能文件夹 | 自然语言触发 |

**快速安装**：将 `drama-skills/` 下的任意技能文件夹（如 `drama-master/`）直接复制到对应平台的技能目录下即可。

---

## 部门架构（27 个角色）

```
drama-master（总入口）
│
├── dept-01-strategy/      战略选题部（4人）
│   ├── drama-market-radar          市场雷达
│   ├── drama-formula-analyst       爆款公式师
│   ├── drama-topic-planner         选题策划官
│   └── drama-project-reviewer      立项复审官
│
├── dept-02-worldbuilding/ 世界构建部（3人）
│   ├── drama-world-architect       世界架构师
│   ├── drama-character-designer    人设设计师
│   └── drama-dream-analyst         梦境指标师
│
├── dept-03-plot-engine/   剧情引擎部（7人）
│   ├── drama-plot-architect        情节架构师
│   ├── drama-hook-designer         钩子设计师
│   ├── drama-conflict-engine       冲突引擎师
│   ├── drama-reversal-master       反转大师
│   ├── drama-rhythm-designer       节奏设计师
│   ├── drama-psychology-architect  心理框架师
│   └── drama-emotion-architect     情绪架构师 ← ScriptForge新增
│
├── dept-04-writing/       创作执行部（3人）
│   ├── drama-script-writer         剧本执笔师
│   ├── drama-dialogue-expert       对白专家
│   └── drama-scene-director        场景导演
│
├── dept-05-review/        评审质控部（4人）
│   ├── drama-script-reviewer       审稿官
│   ├── drama-reader-reviewer       读者视角官
│   ├── drama-emotion-auditor       情绪审计官
│   └── drama-quality-reporter      质量报告官
│
├── dept-06-polish/        修改润色部（3人）
│   ├── drama-script-editor         修稿师
│   ├── drama-pacing-optimizer      节奏优化师
│   └── drama-formatter             格式规范师
│
├── dept-07-production/    制作宣发部（3人）
│   ├── drama-visual-producer       视觉生产官
│   ├── drama-storyboard-director   分镜导演
│   └── drama-marketing-officer     营销策划官
│
└── dept-08-ops/           合规总编室（2人）
    ├── drama-compliance-guard      合规守卫
    └── drama-evolution-analyst     进化分析师
```

---

## 完整创作链路

```
市场雷达 → 爆款公式师 → 选题策划官
         ↓
    立项复审官（通过才继续）
         ↓
世界架构师 → 人设设计师 → 梦境指标师
         ↓
情节架构师 → 钩子设计师 + 冲突引擎师 + 反转大师 + 节奏设计师 + 心理框架师
         ↓
剧本执笔师（对白专家 + 场景导演 协作）
         ↓
审稿官 + 读者视角官 + 情绪审计官 → 质量报告官
         ↓
[不达标] → 修稿师 → 节奏优化师 → 格式规范师 → 返回审稿官
[达标]   → 视觉生产官 + 分镜导演 + 营销策划官
         ↓
合规守卫（最终把关）
         ↓
进化分析师（记录灵感，更新知识库）
```

---

## 进化系统（四轨道）

| 轨道 | 触发 | 内容 |
|------|------|------|
| **轨道一：技能规则** | 评分低于阈值 | 更新角色SKILL.md → PR审批 |
| **轨道二：灵感归档** | 创作中随时 | 钩子/反转/对白/结构 → `inspirations/` |
| **轨道三：外部摄入** | 用户提交内容 | PDF/公众号/GitHub等 → `knowledge/` |
| **轨道四：新模式** | 拉片/摄入发现 | 全新规律 → 验证后升级为规则 |

**外部内容提交方式**：参见 `INTAKE_PROTOCOL.md`（支持GitHub/PDF/公众号/小红书/Word）

详见 `EVOLUTION_LOG.md` 和 `dept-08-ops/drama-evolution-analyst/SKILL.md`。

---

## 网站集成指南

本技能体系设计了清晰的 **输入/输出契约**，可直接映射到网站 API：

```
每个技能 SKILL.md 中包含：
- input_schema: 输入字段定义
- output_schema: 输出字段定义
- 调用示例（可直接封装为 API endpoint）
```

网站搭建建议：
1. 每个部门对应一个工作面板（workflow stage）
2. 每个角色对应一个 AI 节点
3. 角色间数据流向即为 API 调用链
4. `quality-reporter` 的 JSON 输出可直接用于前端评分展示

参考现有实现：`backend/apps/agent/independent_defaults.py`

---

## 文件结构说明

```
drama-skills/
├── README.md                 本文件
├── EVOLUTION_LOG.md          四轨道进化日志
├── INTAKE_PROTOCOL.md        外部内容摄入协议
├── drama-master/             总入口技能
├── drama-intake/             外部内容摄入器
│
├── dept-01-strategy/         战略选题部（5人）
│   └── drama-lapian-analyst/ 拉片分析师 ← dramaskill node-9
├── dept-02-worldbuilding/    世界构建部（3人）
├── dept-03-plot-engine/      剧情引擎部（7人）
│   └── drama-emotion-architect/ 情绪架构师 ← ScriptForge
├── dept-04-writing/          创作执行部（3人）
├── dept-05-review/           评审质控部（4人）
├── dept-06-polish/           修改润色部（3人）
├── dept-07-production/       制作宣发部（3人）
└── dept-08-ops/              合规总编室（2人）
│
├── inspirations/
│   ├── hooks.md              钩子灵感库（含预置示例）
│   ├── reversals.md          反转灵感库（含预置示例）
│   ├── dialogues.md          金句对白库（含预置示例）
│   ├── structures.md         结构创新库（含预置示例）
│   └── new-patterns.md       新模式发现库（待填充）
│
└── knowledge/
    ├── market-insights.md    市场洞察知识库（来自外部摄入）
    └── knowledge-sections.md ScriptForge Tier1规则区块索引
```

---

## 三分支整合说明

### ScriptForge（主库）贡献
- Tier1知识区块体系（17个区块，见 `knowledge/knowledge-sections.md`）
- `emotion_architect` Agent → 情绪架构师角色
- ai_field_prompts（拉片分析AI字段）
- Django 后端技能进化引擎（`RuleEvolutionProposal`）

### dramaskill（节点版）贡献
- Node-9 拉片分析6维度框架 → 拉片分析师角色
- "发现新模式"机制 → 轨道四（新模式发现）
- 5大参考JSON库（hook-library/reversal-patterns等）→ 灵感库预置内容

### dramaskilltrae（Trae版）贡献
- 39个专业技能（钩子设计师/反转大师/合规守卫等）
- drama-master-suite 编排架构
- 梦境三指标理论（dream-indicators）
- 八维评分体系（evaluation-scorer）

## 与 dramaskilltrae 的对应关系

| 本库角色 | 对应 dramaskilltrae 技能 | 新增内容 |
|---------|------------------------|---------|
| drama-master | drama-master-suite | 简化启动流程 |
| drama-market-radar | drama-smart-search | 新增趋势分析 |
| drama-formula-analyst | drama-dream-indicators | 新增公式匹配 |
| drama-hook-designer | drama-plot-hook-designer | S/A/B/C 钩子分级 |
| drama-reversal-master | drama-plot-reversal-engine | 第二反转引擎 |
| drama-conflict-engine | drama-plot-conflict-engine | 冲突升级协议 |
| drama-rhythm-designer | drama-plot-rhythm-engine | 节奏诊断 |
| drama-psychology-architect | drama-plot-psychology-framework | 梦境理论 |
| drama-quality-reporter | drama-evaluation-scorer | 八维评分 |
| drama-compliance-guard | drama-compliance-gate | 多模式合规 |
| drama-evolution-analyst | 新增 | 灵感归档+技能进化 |

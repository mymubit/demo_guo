# Drama Skills 网站建设完整技术方案

> 分析日期：2026-06-22  
> 结论：**在现有 ScriptForge 代码基础上扩建，不推翻重建**

---

## 一、现有代码库盘点

### 已有（无需重写）

| 模块 | 路径 | 覆盖能力 |
|------|------|---------|
| Django 6 后端框架 | `backend/` | 路由/认证/ORM/迁移全套 |
| JWT 认证 | `apps/users/` | 登录/注册/权限 |
| AgentDefinition 模型 | `apps/agent/models.py` | 直接映射36个drama角色 |
| LlmProvider 多模型 | `apps/skill/models.py` | 多Provider配置 |
| AgentLlmRoute 模型 | `apps/agent/models.py` | 每Agent对应模型 |
| LlmService 调用 | `apps/skill/llm/chat.py` | OpenAI兼容接口 |
| LlmUsageLog | `apps/skill/llm/usage_log.py` | Token逐次记录 |
| SkillRuleConfig | `apps/skill/models.py` | Tier1-4规则存储 |
| 流式生成 | `apps/creation/agent_runtime/stream_service.py` | SSE流式输出 |
| 独立Agent运行时 | `apps/creation/agent_runtime/independent_service.py` | Agent执行引擎 |
| Project + Artifact | `apps/creation/models.py` | 项目和产物存储 |
| 计费系统 | `apps/billing/` | Coin消费/充值 |
| React + Vite 前端 | `frontend/` | 全部UI框架 |
| 创作工作台 | `frontend/src/pages/Creation/` | 基础工作台UI |
| Admin后台 | `frontend/src/pages/Admin/` | 运营配置面板 |

### 需要新增/修改

| 优先级 | 内容 | 估计规模 |
|--------|------|---------|
| P0 | 种入36个drama-skills Agent | 1个management command |
| P0 | 种入Tier1-4规则 | 1个management command |
| P1 | 字数验证API | 2个接口 |
| P1 | 交付打包API | 1个接口 |
| P1 | 剧本评级展示 | 1个前端页面 |
| P1 | 双轨创作工作室 | 1个大前端页面 |
| P2 | 每角色模型配置UI | 1个Admin面板 |
| P2 | Token/计费仪表盘 | 1个前端组件 |
| P3 | 风格一致性API | 1个接口 |

---

## 二、架构设计

### 2.1 角色→模型路由设计（关键创新）

```
drama-skill角色 → AgentDefinition → AgentLlmRoute → LlmProvider → 实际模型

示例：
  drama-series-architect → agent_id=drama.series-architect → route: provider=openai, model=gpt-4o
  drama-script-writer  → agent_id=drama.script-writer  → route: provider=deepseek, model=deepseek-chat
  drama-formatter      → agent_id=drama.formatter      → route: provider=claude, model=claude-3-haiku (轻量任务)
```

**为什么不同角色用不同模型：**
- 战略分析角色（市场雷达/公式分析师）：需要联网/新知识，用强推理模型
- 创意写作角色（剧本执笔/对白专家）：需要创意输出，用擅长创作的模型
- 格式检查角色（格式规范师/字数治理）：简单任务，用轻量快速模型
- 质量审查角色（质量报告官）：需要严格评分，用高质量推理模型

### 2.2 工作流状态机

```
项目状态（Project.drama_stage）：
  strategy → worldbuilding → plot_design → writing → review → polish → production → delivered

快速通道（8步）：
  brief → worldbuilding → outline → writing → review → compliance → deliver
  
专家通道（36角色全流程）：
  按部门顺序，每个角色输出作为下一角色的输入
```

### 2.3 数据模型扩展

```python
# 新增 DramaProject 扩展 Project
class DramaProject(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    drama_stage = models.CharField(max_length=32, default='strategy')  # 当前所在阶段
    track_mode = models.CharField(max_length=16, default='fast')  # fast | expert
    total_episodes = models.IntegerField(default=30)
    target_platform = models.CharField(max_length=32, default='douyin')
    genre_code = models.CharField(max_length=32, default='family-revenge')
    word_count_stats = models.JSONField(default=dict)  # 每集字数统计
    quality_scores = models.JSONField(default=dict)    # 10维评分
    delivery_status = models.CharField(max_length=16, default='pending')
```

---

## 三、后端实现计划

### 3.1 P0 - 种入36个Drama-Skills Agent

文件：`backend/apps/agent/management/commands/seed_drama_skills_agents.py`

```python
# 36个角色的AgentDefinition + 对应的AgentPromptVersion
# 每个角色包含：
# - agent_id: drama.{role-name}
# - name_zh: 中文角色名
# - description: 职责说明（来自SKILL.md description字段）
# - category: drama_skills
# - workspace_order: 按流程顺序
# - input_contract: 输入schema
# - output_contract: 输出schema
# - system_prompt: 从SKILL.md提取
```

### 3.2 P0 - 种入Tier1-4规则

文件：`backend/apps/skill/management/commands/seed_drama_tier_rules.py`

```python
# Tier1: 17个通用规则区块（来自knowledge/knowledge-sections.md）
# Tier2: 品类规范（来自knowledge/tier2-genre-rules.md）
# Tier3: 节点流程规则（来自knowledge/tier3-node-rules.md）  
# Tier4: 合规熔断规则（来自knowledge/tier4-compliance.md）
```

### 3.3 P1 - 新增API接口

```
drama_skills/urls.py → 挂载到 /api/drama/

GET  /api/drama/roles/                    # 36角色列表（含部门分组）
GET  /api/drama/roles/{role_id}/          # 角色详情+系统Prompt
POST /api/drama/projects/                 # 创建剧本项目
POST /api/drama/projects/{id}/run/{role}/ # 执行某个角色
GET  /api/drama/projects/{id}/progress/   # 项目进度（哪些角色已完成）
POST /api/drama/validate/word-count/      # 字数验证（输入剧本，返回字数报告）
GET  /api/drama/projects/{id}/quality/    # 质量报告（10维评分）
POST /api/drama/projects/{id}/deliver/    # 触发交付打包
GET  /api/drama/stats/token/              # Token用量统计
GET  /api/drama/stats/billing/            # 计费统计（按角色/时间/项目）
GET  /api/drama/models/config/            # 每角色对应的LLM配置
PUT  /api/drama/models/config/{role_id}/  # 修改角色LLM配置
```

### 3.4 P1 - 字数验证Service

```python
class DramaWordCountService:
    FIRST_EPISODE_MIN = 900
    FIRST_EPISODE_MAX = 1100
    OTHER_EPISODE_MIN = 700
    OTHER_EPISODE_MAX = 900
    DIALOGUE_RATIO_MIN = 0.28
    
    def validate_episode(self, content: str, episode_number: int) -> dict:
        # 1. 清除非剧本内容（AI提示词块等）
        # 2. 统计CJK字符
        # 3. 统计台词字符（角色（情绪）：后的内容）
        # 4. 输出达标/偏短/偏长的报告
```

---

## 四、前端实现计划

### 4.1 新路由规划

```
/drama                           # 剧本创作中心（替代/creation）
/drama/new                       # 新建项目（模式选择）
/drama/workspace/{projectId}     # 项目工作台（36角色面板）
/drama/scripts/{projectId}       # 剧本展示页（多集+评分）
/admin/drama-models              # 模型配置管理
/admin/drama-analytics           # Token+计费分析
```

### 4.2 关键页面设计

#### 创作工作室（/drama/workspace/{id}）

```
┌─────────────────────────────────────────────────────────┐
│  《剧名》  |  30集  |  复仇题材  |  专家通道        [完成度 45%] │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  角色流程    │  当前角色：情节架构师                       │
│  ──────────  │  ────────────────────────────────────    │
│  ✅ 市场雷达 │  [系统Prompt]  [知识规则]  [执行历史]     │
│  ✅ 爆款公式 │                                          │
│  ✅ 选题策划 │  输入：                                  │
│  ✅ 立项复审 │  ┌─────────────────────────────────┐    │
│  ✅ 世界架构 │  │ 上游产物：项目简报、世界观、人物...│    │
│  ✅ 人设设计 │  └─────────────────────────────────┘    │
│  ⟳ 情节架构 │                                          │
│  □ 钩子设计 │  [🚀 执行角色]  [⚙️ 选择模型]            │
│  □ ...      │                                          │
│              │  输出：                                  │
│  [快速通道]  │  ┌─────────────────────────────────┐    │
│  [专家通道]  │  │ 分集大纲（流式生成中...）          │    │
│              │  └─────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────┘
```

#### 剧本展示（/drama/scripts/{id}）

```
┌─────────────────────────────────────────────────────────┐
│  《复仇短剧》  |  30集  |  综合评分: 82分 A级              │
├──────────────────────────────┬──────────────────────────┤
│  集数列表                     │  第1集内容               │
│  ─────────────────────────   │  ─────────────────────── │
│  📗 第1集  1050字 ✅           │  1-1 日 外 朱雀门楼      │
│  📗 第2集   820字 ✅           │  人物：夏倾凰、秦桧       │
│  📗 第3集   780字 ✅           │                         │
│  📘 第4集   650字 ⚠️偏短       │  △【全景】残阳如血...    │
│  ...                         │                         │
│                               │  秦桧（阴冷）：陛下...   │
│  字数统计：                   │  夏倾凰（冷笑）：...      │
│  ████████ 平均 835字           │                         │
│  台词占比 32% ✅               │  ─── 字数: 1050 ✅ ───  │
│                               │  台词: 320字(30.5%) ✅   │
│  10维评分雷达图                 │  场景: 2个 ✅            │
│     格式 88                   │                         │
│  商业  结构                   │                         │
│    梦境 人物                  │                         │
│    情绪  对白                  │                         │
│       钩子                    │                         │
└──────────────────────────────┴──────────────────────────┘
```

#### 模型配置（/admin/drama-models）

```
┌─────────────────────────────────────────────────────────┐
│  模型配置中心  |  按角色分配LLM模型                        │
├──────────────────────────────────────────────────────────┤
│  部门          │ 角色         │ 当前模型        │ 操作   │
│  ─────────────────────────────────────────────────────  │
│  战略选题部    │ 市场雷达     │ GPT-4o          │ [修改] │
│               │ 爆款公式师   │ GPT-4o          │ [修改] │
│  剧情引擎部   │ 情节架构师   │ Claude-3.5      │ [修改] │
│               │ 钩子设计师   │ Claude-3.5      │ [修改] │
│  创作执行部   │ 剧本执笔师   │ DeepSeek-V3     │ [修改] │
│               │ 对白专家     │ DeepSeek-V3     │ [修改] │
│  修改润色部   │ 格式规范师   │ Claude-3-Haiku  │ [修改] │
│               │ 字数治理官   │ Claude-3-Haiku  │ [修改] │
│  ...          │ ...          │ ...             │ ...    │
└──────────────────────────────────────────────────────────┘
```

---

## 五、Token 计费设计

### 5.1 现有基础

- `LlmUsageLog`：已记录每次调用的 prompt_tokens、completion_tokens、total_tokens、cost_cents
- `Billing` app：已有 Coin 体系

### 5.2 新增统计维度

```python
# 在 LlmUsageLog 上扩展，或通过聚合查询实现：

# 按角色统计
{
  "role": "drama.script-writer",
  "total_calls": 120,
  "total_tokens": 850000,
  "avg_tokens_per_call": 7083,
  "total_cost_yuan": 12.5
}

# 按项目统计
{
  "project_id": "xxx",
  "project_name": "《复仇短剧》",
  "total_tokens": 1200000,
  "total_cost_yuan": 18.0,
  "breakdown_by_role": {...}
}

# 按时间统计（日/周/月）
```

### 5.3 前端仪表盘组件

```
Token 用量仪表盘：
├── 今日 Token 用量（折线图）
├── 按角色 Token 分布（饼图）
├── 按模型 Token 分布（柱状图）
├── 按项目 Token 分布（Top 10）
└── 费用趋势（折线图，按日/周/月切换）
```

---

## 六、实施顺序

### Phase 1（立即实施）
1. `seed_drama_skills_agents.py` — 36角色注入DB
2. `seed_drama_tier_rules.py` — Tier1-4规则注入DB
3. Drama API 路由 + 核心接口（7个）
4. 字数验证 Service

### Phase 2（Phase 1完成后）
5. 创作工作室前端页面（双轨模式）
6. 剧本展示页（评分雷达图）

### Phase 3（后续迭代）
7. 模型配置Admin面板
8. Token/计费仪表盘

---

## 七、关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 是否推翻重建 | **不推翻** | 70%+基础设施已有，重建浪费 |
| 角色执行引擎 | 复用 IndependentAgentService | 已经过验证的流式执行引擎 |
| 流式生成 | Server-Sent Events (SSE) | 现有实现完整 |
| 前端状态管理 | Zustand（已有）+ React Query | 现有技术栈 |
| 评分图表 | Recharts（需安装）| 轻量，React友好 |
| 字数统计 | 纯Python字符计数 | 简单高效 |

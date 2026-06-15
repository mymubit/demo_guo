# creation/orchestration 模块架构说明

## 职责分层

```
creation/
├── services.py                  ← 创作公共服务（提交、进度、下载、分享）
├── workspace_service.py         ← 工作台层：五步 Agent 独立生成控制
│   负责 trigger_skill_generation / save_workspace_skill，扣币、进度广播
├── execution_run_service.py     ← 执行轨迹追踪：AgentExecutionRun CRUD
│   负责创建/更新执行记录，供监察中心查询
├── convergence_service.py       ← 收敛服务：质检、评分、门控
│   负责判断节点是否通过质量门控
├── artifact_service.py          ← 产物读写：融合产物 JSON 的 get/save
│
└── orchestration/               ← 编排调度中心
    ├── orchestrator.py          ← 统一调度入口（选择运行器、协调节点链路）
    ├── workspace_bridge.py      ← 工作台与编排器的桥接层
    ├── llm_node_engine.py       ← LLM 节点执行引擎
    ├── agent_payload.py         ← Agent Payload 构建（Prompt、上下文组装）
    ├── quality_guard.py         ← 质量守卫（门控、缺陷记录）
    ├── sub_skill_orchestrator.py ← 子技能编排（批量集数、大纲批次）
    ├── sub_skill_runner.py      ← 子技能单次执行
    │
    ├── brief/                   ← Brief Agent（立项简报）
    ├── world/                   ← WorldAgent（结构世界观）
    ├── character/               ← CharacterAgent（人物体系）
    ├── outline/                 ← OutlineAgent（分集大纲）
    ├── script/                  ← ScriptAgent（剧本正文）
    ├── adapt/                   ← AdaptAgent（小说改编）
    ├── polish/                  ← PolishAgent（润色精修）
    ├── marketing/               ← MarketingAgent（营销素材）
    │
    ├── emotion_architect.py     ← 情绪节奏架构分析
    ├── review.py                ← 质量审查协调
    ├── score.py                 ← 评分计算
    └── insight.py               ← 洞察分析
```

## 调用链

```
portal/creation/views.py
  └─► CreationService (services.py)
        ├─► trigger_skill_generation → workspace_service.py
        │     └─► orchestrator.py (AgentOrchestrator)
        │           └─► llm_node_engine.py → LLM Provider
        └─► convergence_service.py (质量门控)
```

## 关键约定

- **workspace_service** 负责外部入口（鉴权、扣币、任务入队），**orchestrator** 负责纯编排逻辑
- **execution_run_service** 只做轨迹记录，不包含业务逻辑
- **artifact_service** 只做 JSON 产物的 DB 读写，不做转换
- 所有 Agent 子模块（brief/world/character/...）仅负责构建 Prompt 和解析 LLM 响应
- 严禁在 orchestration/ 内直接修改 Project 状态，状态变更必须通过 services.py 或 workspace_service.py

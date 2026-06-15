# apps/agent 目录说明

Agent 中心 — 技能注册表、步骤绑定、子技能链、LLM 路由、质检策略。

```
agent/
├── models.py       # AgentRegistryConfig, AgentLlmRouteConfig, ReviewScoringConfig
├── registry.py     # AgentRegistryConfigService（Admin 读写）
├── runtime.py      # get_agent_registry 运行时缓存
├── catalog.py      # portal_agent_catalog
├── binding.py      # 流水线 index → agent_id 绑定
├── routes.py       # AgentLlmRouteService
└── bootstrap/      # tier1、agent_llm_routes 种子
```

索引：`backend/CENTERS.md`

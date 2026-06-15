# console 后台 API — 按十大中心组织

```
console/
├── agent/           # Agent 中心 — registry、llm-routes、review-scoring、catalog
├── main_chain/      # 主链工作室 — 蓝图聚合 API
├── workflow/        # workflow 步骤/fusion 视图（挂载于 main-chain 前缀）
├── orchestration/   # 调度中心 — 执行轨迹、sub-skill 统计
├── skills/          # 技能中心 — 规则库
├── config/          # 配置中心 — 门户 catalog、themes、hooks
├── model/           # 模型中心 — LLM Provider
├── creation/        # 创作中心 — 项目监察
├── identity/        # 用户中心
├── commerce/        # 商业中心
└── monitor/         # 监控中心
```

新 URL 前缀见 `backend/CENTERS.md`；旧路径保留双路由兼容。

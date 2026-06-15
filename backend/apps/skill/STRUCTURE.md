# apps/skill 目录说明（收窄后）

`skill` Django App 承载 **技能中心**、**配置中心（portal）**、**模型中心**。

```
skill/
├── skills/              # 技能中心 — 仅 loader + admin_service（写作规则）
├── config/portal/       # 配置中心 — 创作表单、题材、参考库
├── config/bootstrap/    # 种子（非 workflow/agent）
└── llm/                 # 模型中心
```

**已迁出**：
- Agent 注册表 → `apps/agent/`
- 流水线/Fusion → `apps/workflow/`

索引：`backend/CENTERS.md`

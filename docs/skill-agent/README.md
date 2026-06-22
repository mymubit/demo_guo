# Skill & Agent 实施文档索引

独立 Agent 主架构下的 Skill SSOT 与运行时实施文档集。总纲：[00-MASTER-ARCHITECTURE.md](./00-MASTER-ARCHITECTURE.md)。

## A. 总纲与架构

| 文档 | 说明 |
|------|------|
| [00-MASTER-ARCHITECTURE.md](./00-MASTER-ARCHITECTURE.md) | 总架构、SSOT 优先级、API 索引 |
| [01-AGENT-SKILL-USER-LAYERS.md](./01-AGENT-SKILL-USER-LAYERS.md) | Agent / Skill / User 三层 Prompt |
| [02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md) | Fusion 删除计划 |

## B. 数据模型与 SSOT

| 文档 | 说明 |
|------|------|
| [10-DATA-LAYER-MAP.md](./10-DATA-LAYER-MAP.md) | 分层表与读写入口 |
| [11-SKILL-RULE-ITEM-SPEC.md](./11-SKILL-RULE-ITEM-SPEC.md) | 规则原子化 |
| [12-AGENT-SKILL-DEFINITION-SPEC.md](./12-AGENT-SKILL-DEFINITION-SPEC.md) | AgentSkill 生命周期 |
| [13-CATALOG-ATOMIC-SPEC.md](./13-CATALOG-ATOMIC-SPEC.md) | Theme/Form/Scoring 原子化 |
| [14-SKILL-CONFIG-ENTRY-MATRIX.md](./14-SKILL-CONFIG-ENTRY-MATRIX.md) | config_key 矩阵 |
| [15-DATA-INTEGRITY-FIXES.md](./15-DATA-INTEGRITY-FIXES.md) | 完整性修复清单 |

## C. 迁移与运维

| 文档 | 说明 |
|------|------|
| [20-MIGRATION-RUNBOOK.md](./20-MIGRATION-RUNBOOK.md) | 迁移命令顺序 |
| [21-ADMIN-OPERATIONS-GUIDE.md](./21-ADMIN-OPERATIONS-GUIDE.md) | 运营 SOP |
| [22-VERSION-GRAY-RELEASE.md](./22-VERSION-GRAY-RELEASE.md) | 版本与灰度 |

## D. 独立 Agent 运行时

| 文档 | 说明 |
|------|------|
| [30-INDEPENDENT-AGENT-RUNTIME.md](./30-INDEPENDENT-AGENT-RUNTIME.md) | run 全链路 |
| [31-JSON-SELF-HEAL-SPEC.md](./31-JSON-SELF-HEAL-SPEC.md) | JSON 自修复 |
| [32-PROJECT-CONTEXT-MEMORY.md](./32-PROJECT-CONTEXT-MEMORY.md) | Project 记忆 |
| [33-ENTRY-PLAN-ROUTING.md](./33-ENTRY-PLAN-ROUTING.md) | 入口 Plan |

## E. 流式生成

| 文档 | 说明 |
|------|------|
| [40-STREAMING-GENERATION-SPEC.md](./40-STREAMING-GENERATION-SPEC.md) | SSE + 增量 JSON |
| [41-CHUNK-PERSISTENCE-API.md](./41-CHUNK-PERSISTENCE-API.md) | Chunk 持久化 API |

## 实施阶段

| Phase | 文档 | 代码目标 |
|-------|------|----------|
| 0 | 02, 20 | 删 Fusion 主路径 |
| 1 | 11, 15, 20 | SkillRuleItem 全量 + CRITICAL 修复 |
| 2 | 12, 30, 21 | Agent/Knowledge 统一 |
| 3 | 31, 32, 33 | 自修复、记忆、Plan |
| 4 | 40, 41 | 流式 + Chunk |
| 5 | 13, 14, 22 | Catalog 原子化、灰度 |

## 相关文档

- [CREATION-BUSINESS-ARCHITECTURE.md](../CREATION-BUSINESS-ARCHITECTURE.md)
- [TECH-ARCHITECTURE.md](../TECH-ARCHITECTURE.md)
- [AGENTS.md](../../AGENTS.md)

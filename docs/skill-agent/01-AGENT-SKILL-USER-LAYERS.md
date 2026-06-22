# Agent / Skill / User 三层 Prompt 边界

> 对应 PDF「角色骨架 + 技能肌肉 + 用户血肉」结论，映射到 ScriptForge 独立 Agent 实现。

---

## 1. 目标

明确 System / User Prompt 各层数据来源，禁止在 View 或前端组件内拼装大段 Prompt。

## 2. 三层对照表

| 概念 | 职责 | 代码映射 | 典型内容 |
|------|------|----------|----------|
| **Agent 层** | 角色定位 + 输出契约 | `AgentDefinition` + `AgentPromptVersion.system_prompt` | 「你是短剧剧本创作总监…」 |
| **Skill 层** | 规则、知识、格式约束 | `AgentKnowledgeItem`（binding）+ `SkillRuleItem` + 可选 `AgentSkillDefinition` | Tier 铁律、品类规范、schema 提示 |
| **User 层** | 本次任务的具体输入 | `Project` 字段 + `ProjectFusionArtifact` + `params` | 主题、集数、上游大纲/人设 JSON |

## 3. 组装顺序（实现）

`IndependentAgentService._prepare_prompt()`：

1. `build_agent_input()` — 读 `input_contract.project_fields`、required/optional artifacts
2. `load_knowledge()` — 按 `AgentKnowledgeBinding` + `knowledge_injection_policy` 过滤注入
3. `render_agent_prompt()` — 渲染 `user_prompt_template`，追加 `output_format_prompt`、`constraints_prompt`、`_artifact_key_hint()`

**System Prompt 来源**：当前以 `AgentPromptVersion.system_prompt` 为主；Tier 规则通过 Knowledge 绑定（category=`rule` / `prompt_section`）或后续统一注入点写入，**不**再经 `FusionPromptBuilder`。

**User Prompt 来源**：模板变量 `{{ project.theme }}`、`{{ artifacts.series_outline }}` 等，roots 见 `_template_roots()`。

## 4. Agent 与 AgentSkillDefinition 关系

| 路径 | 用途 | 主路径 |
|------|------|--------|
| `AgentDefinition` + Knowledge | C 端用户运行 | **是** |
| `AgentSkillDefinition` | 工具/Cursor 拉取 SKILL.md、legacy skill_id 映射 | 辅助 SSOT |

实施约定（见 [12-AGENT-SKILL-DEFINITION-SPEC.md](./12-AGENT-SKILL-DEFINITION-SPEC.md)）：

- C 端 `execute_run` **只读** `AgentDefinition` 链路。
- 将 `AgentSkillDefinition.content` 同步为 `AgentKnowledgeItem`（import 命令），或通过 binding 引用，避免双份 Prompt 漂移。

## 5. SkillRuleItem 在 Skill 层的地位

- 运行时：`SkillRuleLoader.load_rule_items()` 优先查 `SkillRuleItem`（`status=active`, `item_type=rule`），渲染为 `- title: body` 文本块。
- 注入方式：作为 Knowledge 条目导入，或在 `load_knowledge` 前合并 global compliance 片段（实现阶段二统一）。

## 6. 禁止事项

- 在 `portal/creation/views.py` 内拼接 Tier 规则字符串
- 在前端 `IndependentAgentWorkspace.jsx` 内构造 system prompt
- 同时维护 `AgentSkillDefinition.content` 与 `AgentPromptVersion` 两份 SSOT 而不同步

## 7. 测试矩阵

| 类型 | 用例 |
|------|------|
| normal | 有 required artifacts 时 user_prompt 含 JSON 块 |
| boundary | `max_prompt_tokens` 超限时 preview 返回 `within_limit=false` |
| error | 模板含未解析 `{{` 抛出 `AgentRuntimeError` |
| permission | 非 owner 无法 trigger run |

## 8. 旧逻辑删除

- 删除对 `FusionPromptBuilder.build()`、`build_full_system_prompt(tier1-4)` 作为主链的依赖。
- Tier3 `node-*` scope 数据**保留**，改绑到 Agent Knowledge 或按 agent_id 过滤 Item。

参考：[02-LEGACY-REMOVAL-PLAN.md](./02-LEGACY-REMOVAL-PLAN.md)、[30-INDEPENDENT-AGENT-RUNTIME.md](./30-INDEPENDENT-AGENT-RUNTIME.md)。

# JSON 输出自修复规范

---

## 1. 目标

降低 LLM 返回非法 JSON 导致的 run 失败率；**不**引入通用 Agent 动态路由。

## 2. 背景（PDF 借鉴 #1）

当前：`IndependentAgentService.extract_json_object()` 失败即 `AgentRuntimeError`。

目标：格式错误时追加 1–2 轮「修复 LLM」调用。

## 3. 接入点

文件：`backend/apps/creation/agent_runtime/independent_service.py`

```
execute_run 内：
  response = llm.chat(...)
  try:
      output = extract_json_object(response)
  except AgentRuntimeError as e:
      if not is_format_error(e):
          raise
      output = self_heal_json(response, schema, e, route)
  validate_output(agent, output)
```

## 4. 错误分类

| 类型 | 可自愈 | 处理 |
|------|--------|------|
| JSONDecodeError / 缺闭合括号 | 是 | self_heal |
| 顶层非 object | 部分 | self_heal + 仍失败则 fail |
| schema 字段缺失/类型错 | 否 | 直接 fail 或业务重试策略 |
| artifact_key 非法 | 否 | 已有 fallback default_key |

## 5. self_heal 协议

**输入 messages**：

```text
System: 你是 JSON 修复助手。只输出一个合法 JSON 对象，不要 markdown。
User:
原输出：
{raw_text}

错误：
{error_message}

目标 Schema 摘要：
{schema_hint}

请输出修复后的 JSON。
```

**约束**：

- 最多 `MAX_JSON_HEAL_ATTEMPTS = 2`
- 使用同一 route 或更便宜 model（runtime_policy.json_heal_model）
- 不计入用户-facing 重试次数展示

## 6. Schema 摘要来源

`agent.output_contract.schema_version` → `SCHEMA_FIELD_HINTS` + Knowledge binding OUTPUT_SCHEMA。

## 7.  observability

`AgentExecutionRun` 扩展（或 input_snapshot 内）：

```json
{ "json_heal_attempts": 1, "json_heal_success": true }
```

## 8. 测试矩阵

| 类型 | 用例 |
|------|------|
| normal | 合法 JSON 不触发 heal |
| boundary | trailing comma 修复成功 |
| error | 2 次 heal 仍失败 → run failed |
| permission | 无额外扣费或按 policy 单次 heal 扣币 |

## 9. 旧逻辑删除

Fusion 子技能 CLI 内 JSON 修复 — 合并到统一 self_heal 服务，删重复逻辑。

参考：[30-INDEPENDENT-AGENT-RUNTIME.md](./30-INDEPENDENT-AGENT-RUNTIME.md)。

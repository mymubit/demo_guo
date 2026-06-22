# 流式生成规范（Plan D）

> **状态**：已实现（`chat_stream.py`、`streaming_json_parser.py`、`invoker_stream.py`、`views_stream.py`）。

---

## 1. 目标

`episode_scripts`、`series_outline` 等大数组 Artifact 边生成边展示，降低等待与超时失败。

## 2. 方案选型（PDF）

| 方案 | 说明 | 采纳 |
|------|------|------|
| A | Worker 循环多批，批完刷新 | 过渡 |
| B | 前端轮询 | 过渡 |
| C | SSE 推送每集 | 推荐组合 |
| **D** | LLM token 流 + 增量 JSON 解析 + SSE | **主方案** |

挂载方式：独立 Agent run 的 **stream 变体**：

```
POST /api/creation/projects/<id>/agents/<agent_id>/stream/
```

或 query `?stream=1` on run（需评估与 dj_queue 兼容性 — 长连接建议同步 stream 视图，非 Celery）。

## 3. 模块设计

| 模块 | 路径 | 职责 |
|------|------|------|
| LLM 流 | `apps/skill/llm/chat_stream.py` | `_post_chat_completion_stream()` → (full_text, delta) |
| 增量解析 | `apps/skill/skills/streaming_json_parser.py` | `IncrementalJsonArrayParser` 从流中 yield 完整 object |
| 编排 | `apps/skill/skills/invoker_stream.py` | 生命周期 + 事件枚举 |
| SSE 视图 | `apps/portal/creation/views_stream.py` | `StreamingHttpResponse` |

与 [`IndependentAgentService`](../../backend/apps/creation/agent_runtime/independent_service.py) 关系：stream 路径复用 `_prepare_prompt()`，替换单次 `chat()` 为 `chat_stream()`。

## 4. SSE 事件协议 v1.2

```
event: start
data: {"skill_id":"...", "trace_id":"...", "protocol_version":"1.2", "total_episodes":20, "continue_from":null}

event: token
data: {"delta":"...", "token_index":5}
# 仅第一个 item 出现前发送；150ms 节流

event: item
data: {"data":{...}, "item_index":0, "item_id":"...", "effective_index":1}

event: done
data: {"count":20, "duration_ms":15420, "finalize_status":"ok|truncated"}

event: error
data: {"message":"...", "code":500, "trace_id":"..."}
```

响应头：

```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

## 5. 增量 JSON 解析要点

支持形态：

- `[{...}, {...}]`
- `{"episodes": [{...}]}`
- 单 object 根（非数组技能）

要求：

- 只认 JSON 双引号字符串边界
- code block 前缀 ` ```json ` 跨 chunk 剥离（`_strip_offset`）
- `JSONDecodeError` 继续扫描后续内容
- buffer 收缩防 O(2) 内存

## 6. 可靠性

| 机制 | 参数 |
|------|------|
| Watchdog | 120s 无新 token → error 事件 |
| Client disconnect | GeneratorExit → 停止 LLM 流 |
| 用户并发 | 每 user 每 agent 最多 1 active stream |
| Provider 降级 | 主 provider 失败尝试 fallback_provider_id |
| 校验前置 | skill_id / project_id / 并发 — 进 generator 前返回 4xx |

## 7. 前端

| 组件 | 路径 |
|------|------|
| SSE 客户端 | `frontend/src/services/creation.js` — `streamAgent()` |
| Hook | `frontend/src/hooks/useSkillStream.js` |
| 虚拟列表 | `frontend/src/components/creation/ProjectChunksVirtualList.jsx` |

**不用**原生 `EventSource`（需 POST body）；用 `fetch` + `getReader()`。

## 8. 适用 Agent

| agent output | 数组字段 |
|--------------|----------|
| episode_scripts | episodes[] |
| series_outline | episodes[] / stages[] |

非数组 Agent（review_report）可仅 token 流 + 最终 item 一次。

## 9. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | 20 集 mock 流 → 20 item 事件 |
| boundary | 转义引号、code block 前缀 |
| error | 中途 disconnect → truncated |
| permission | 非 owner 403 |

自动化测试：`apps/creation/tests/test_streaming_and_chunks.py`（含 `IncrementalJsonArrayParserTests`）。

## 10. 旧逻辑删除

- 旧 workspace `generate_skill` 批处理轮询 UX — 由 stream 取代
- Fusion 单次 LLM 生成全集 — 删除

参考：[41-CHUNK-PERSISTENCE-API.md](./41-CHUNK-PERSISTENCE-API.md)。

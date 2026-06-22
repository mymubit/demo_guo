# 分片持久化与 Chunk API

> **状态**：已实现（`ProjectChunk`、`SkillGenerationLog` 模型与 Chunk/SSE API 已落地）。

---

## 1. 目标

流式生成每识别一集即落库；刷新页面可恢复；支持断点续生。

## 2. 数据模型

> 迁移：`creation.0026_agent_notes_chunks_generation_log`。

### 2.1 ProjectChunk

```python
class ProjectChunk(models.Model):
    project = FK(Project)
    kind = CharField  # episode_scripts | series_outline
    index = PositiveIntegerField  # 集号/序号，DB 权威
    data = JSONField  # 单集对象
    run = FK(AgentExecutionRun, null=True)
    created_at = DateTimeField
    class Meta:
        unique_together = [("project", "kind", "index")]
```

### 2.2 SkillGenerationLog

```python
class SkillGenerationLog(models.Model):
    trace_id = CharField(db_index=True)
    skill_id / agent_id = CharField
    user = FK(User)
    project = FK(Project, null=True)
    prompt_tokens / completion_tokens / total_tokens = Int
    provider / model = CharField
    duration_ms = Int
    status = CharField  # ok | error | truncated
    error_message = TextField(blank=True)
```

写入时机：`invoker_stream` 每 yield item 写 Chunk；done/error 写 Log。

## 3. API

前缀建议：`/api/creation/`（与 [CREATION-BUSINESS-ARCHITECTURE.md](../CREATION-BUSINESS-ARCHITECTURE.md) 一致）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `projects/<id>/agents/<agent_id>/stream/` | SSE 流（见 [40-STREAMING-GENERATION-SPEC.md](./40-STREAMING-GENERATION-SPEC.md)） |
| GET | `projects/<id>/chunks/` | 分页列表 |
| POST | `projects/<id>/chunks/continue/` | 断点续生 |

### 3.1 GET chunks

Query：

| 参数 | 默认 |
|------|------|
| kind | episode_scripts |
| limit | 50 |
| offset | 0 |

Response data：

```json
{
  "items": [{ "index": 1, "data": {...} }],
  "total": 80,
  "has_more": true,
  "last_episode_index": 12
}
```

`last_episode_index` 由 DB `Max(index)` 计算，非前端自增。

### 3.2 POST continue

Body：

```json
{
  "agent_id": "episode_scripts",
  "to_episode": 80,
  "params": {}
}
```

服务端：`from_episode = last_episode_index + 1`，调 stream generator。

Stream 请求可选 `continue_from` 显式指定起点。

## 4. effective_index 语义

| 场景 | effective_index |
|------|-----------------|
| 首次生成第 1–5 集 | 1..5 |
| continue_from=13 | 首 item effective_index=13 |
| item 事件 | 必带，UI 显示集号 |

前端 **禁止** 用 `items.length` 推断集号。

## 5. Prompt 缓存（可选）

`invoker_stream` 对相同 payload sha256 命中内存/Redis 缓存，start 事件 `cached: true`。

生产多实例 → Redis；键 TTL 与版本 tag 绑定。

## 6. 计费

| 策略 | 说明 |
|------|------|
| 按批 | 每 N 集扣一次 creation.script 等价币 |
| 流式 | 每 run 按 `pipeline.node.*` 扣费；失败自动回补（`agent_billing.py`） |

## 7. 前端集成

```javascript
// 首次
creation.streamSkill(agentId, { project_id, from_episode: 1, to_episode: 20 }, callbacks)

// 恢复
const { items, last_episode_index } = await creation.listChunks(projectId, kind, limit, offset)

// 续写
creation.continueSkill(agentId, projectId, { to_episode: 80 }, callbacks)
```

Hook：`useSkillStream` — running 锁、abort、total_episodes 进度。

## 8. 测试矩阵

| 类型 | 验收 |
|------|------|
| normal | 流式 3 集 → DB 3 Chunk |
| boundary | offset 分页与流式去重 kind-index |
| error | Chunk 写失败记日志不 silent |
| permission | chunks 仅 owner |

## 9. 旧逻辑删除

- 仅内存 hold 生成结果、刷新丢失 — 删除
- Legacy batch_meta 无持久化 — 删除

参考：[40-STREAMING-GENERATION-SPEC.md](./40-STREAMING-GENERATION-SPEC.md)、[30-INDEPENDENT-AGENT-RUNTIME.md](./30-INDEPENDENT-AGENT-RUNTIME.md)。

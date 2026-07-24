# V3 多 Key 轮询 + 项目看板 — 设计

> 2026-07-23 · 决策 D（A+B）· 支付不做 · 连续执行

## A 多 Key

- 表 `V3LlmProviderKey`：provider FK、label、api_key_encrypted、sort_order、is_enabled
- Provider 主 Key 仍为 `api_key_encrypted`（视为 sort_order=0）
- `chat_with_failover`：同一 ProviderHop 内先轮询主 Key + 附加 Key，可切换错误才换下一供应商
- API：`GET/POST /api/v3/models/providers/{id}/keys/`；`PATCH/DELETE .../keys/{key_id}/`
- ModelsPage：供应商详情可管理附加 Key（只回传 api_key_set）

## B 仪表盘

- 视图切换：列表 / 看板（按 stage 列）
- 搜索：标题本地过滤
- 筛选：stage、entry_type（可选最小：搜索+视图）

## 里程碑

| P5-W1 | 多 Key 模型+路由+API+Models UI |
| P5-W2 | Dashboard 看板/搜索 + 全量基线 |

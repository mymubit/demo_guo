# Models 供应商卡片内联定价 — 设计

> 日期：2026-07-24  
> 状态：已批准（方案 1）  
> 前置：P2-W2 `V3ModelPrice` + `GET/PUT /api/v3/models/prices/` 已落地；Usage 页按单价估费

## 1. 目标

在 `/models` 每个供应商卡片上直接配置「输入/输出 元/1K tokens」，保存后 `/usage` 能显示估算费用；双空保存表示未定价。

## 2. 决策

| 点 | 选择 |
|----|------|
| 入口位置 | 嵌在供应商卡片内（非独立页、非编辑弹窗） |
| 交互 | 卡片上两个可编辑数字框 +「保存定价」 |
| 清空语义 | 两边都空 → 删除单价行 → Usage「未定价」 |
| 币种 | 固定 `CNY`，UI 不展示 |
| `model_name` | 绑定供应商当前 `model_name`，不另编辑 |
| 后端删行 | 新增 `DELETE /api/v3/models/prices/{id}/`；PUT 仍只 upsert |

## 3. API

### 既有

- `GET /api/v3/models/prices/` → `{ items: ModelPrice[] }`
- `PUT /api/v3/models/prices/` body `{ items: [...] }` — 按 `provider_id + model_name` upsert（不删未出现的行）

### 新增

- `DELETE /api/v3/models/prices/{id}/`
  - 存在：删除，返回 `{ deleted: true, id }`（或空 data + code 0）
  - 不存在：404

## 4. 前端（ModelsPage）

- 页面加载并行拉取 providers + prices（及既有 mappings）
- 每卡回填：匹配 `provider_id` 且 `model_name === provider.model_name` 的价；无则空
- 校验：两边都填（≥0）或都空；只填一边拦截并提示
- 有值保存 → `PUT` 单条 item（`currency: "CNY"`）
- 双空保存 → 若有对应 price `id` 则 `DELETE`；无则 no-op
- 保存成功后 invalidate prices query

## 5. 不在范围

- 新路由、支付/配额、历史 rollup 重算、同一供应商多 `model_name` 多价 UI、币种切换

## 6. 验收

1. 设单价后 Usage 对应模型行出现非「未定价」估算（有 token 的前提下）
2. 清空保存后变回「未定价」
3. 后端：DELETE 成功/404；PUT/GET 回归仍绿
4. 前端 vitest：回填、PUT 保存、清空 DELETE、单边空校验

## 7. 自检

- 无占位符；与既有 PUT「不全量替换」行为一致
- 清空依赖 DELETE，不滥用空 PUT
- 范围仅 Models 卡片 + DELETE 端点

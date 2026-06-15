# Fullstack Legacy Compat Removal — 详细参考

## 引用扫描与遗留模式检索

对每一批拟删的符号、分支、别名，先扫描再改。

### 前端（React）

```bash
# 旧列表结构
rg "result\.items|data\.items|\.items\s*\?\?" frontend/src/services frontend/src/pages --glob '*.{js,jsx,ts,tsx}'

# 双字段兼容
rg "task_id|project_id" frontend/src/services frontend/src/pages --glob '*.{js,jsx}'

# legacy / 兼容 / TODO 移除
rg -i "legacy|compat|旧版|兼容|deprecated|TODO.*移除" frontend/src/services frontend/src/adapters

# 旧路由或 v1 路径
rg "/api/v1/|/api/works/|/api/tasks/" frontend/src/services

# barrel 别名 re-export
rg "export \{.* as |export \* from|保持与旧版|仅作聚合" frontend/src/services

# 谁还在 import 旧名
rg "from ['\"]@/services/api['\"]|from ['\"]./api['\"]" frontend/src/
rg "API_BASE[^_]|adminMainChain|normalizeCreationSubmitResult" frontend/src/
```

### 后端契约核对（Django）

```bash
# 标准分页
rg "StandardPagination|get_paginated_response" backend/apps

# 创作新版路由
rg "creation/fusion|agents/catalog" backend/apps --glob '**/urls.py'

# 字段名（确认新版唯一字段）
rg "project_id|task_id" backend/apps --glob '**/{serializers,views,models}.py'
```

**判定**：引用为零且非动态 import → 可删；页面仍 import 旧别名 → 先改 import 再删 export。

---

## 常见删除模式对照

### 1. 列表适配器 — 去掉 `{items}` 分支

**删除前（过渡写法）：**

```javascript
export function normalizeListResult(result, itemMapper = (item) => item) {
  const items = Array.isArray(result?.data)
    ? result.data
    : Array.isArray(result?.items)
      ? result.items
      : []
  const pagination = result?.pagination ?? result?.meta?.pagination ?? {}
  // ...
}
```

**删除后（仅新版）：**

```javascript
export function normalizeListResult(result, itemMapper = (item) => item) {
  const items = Array.isArray(result?.data) ? result.data : []
  return {
    items: items.map(itemMapper).filter(Boolean),
    pagination: normalizePagination(result?.pagination),
    facets: result?.facets,
    meta: result?.meta,
  }
}
```

**说明**：HTTP 层 `parseResponse` 已在 `code === 0` 时解包为 `{ data, pagination }`；adapter 不再猜测 `items`。

### 2. HTTP 解包 — 去掉无 `code` 直返

**删除前：**

```javascript
// 兼容旧版：无 code 字段时按 HTTP 200 直接返回
return raw
```

**删除后：**

```javascript
if (typeof raw.code !== 'number') {
  throw createApiError({ message: 'Invalid response shape', code: -1, data: raw })
}
// 仅处理 code === API_SUCCESS_CODE 分支
```

保留 `rawResponse: true` 的文件下载等特殊接口，不在此删。

### 3. 创作模块 — 去掉 task_id / project_id 双读

**删除前：**

```javascript
export function normalizeCreationSubmitResult(raw) {
  if (!raw) return raw
  return {
    ...raw,
    project_id: raw.project_id ?? raw.task_id,
    task_id: raw.task_id ?? raw.project_id,
  }
}
```

**删除后：**

```javascript
export function normalizeCreationSubmitResult(raw) {
  if (!raw) return raw
  return raw  // 或仅映射后端稳定 snake_case → 前端 camelCase，无双字段兜底
}
```

页面层统一使用后端文档指定的唯一 ID 字段（通常为 `project_id`）。

### 4. works 详情 — 去掉 HTML / 快照双字段

**删除前：**

```javascript
resultHtml: work.rendered_result_html || work.result_html || '',
gateSummary: fusionSnapshot.gateSummary || fusionSnapshot.gate_summary || null,
```

**删除后（字段名以后端 Serializer 为准）：**

```javascript
resultHtml: work.rendered_result_html ?? '',
gateSummary: fusionSnapshot.gate_summary ?? null,
```

仅保留后端实际返回的 canonical 字段名；UI 层禁止再写 `||` 链读旧名。

### 5. 订单 / 会员 — 去掉旧接口与旧嵌套

**删除前：**

```javascript
plan_name: raw.membership_plan?.name || raw.plan_name || raw.plan?.title,
```

**删除后：**

```javascript
plan_name: raw.membership_plan?.name ?? raw.plan_name,
```

若后端已扁平化，则只保留一层：`plan_name: raw.plan_name`。

### 6. barrel 旧别名 — 删除并统一 import

**删除前（api.js）：**

```javascript
export { API_BASE_URL as API_BASE } from './http'
export default { /* ... */, API_BASE: API_BASE_URL }
```

**步骤：**

1. `rg "API_BASE[^_]" frontend/src` 列出全部引用；
2. 批量改为 `API_BASE_URL` 或从 `./http` 直接 import；
3. 删除 `as API_BASE` 与 default 对象上的重复键；
4. 无引用后考虑删除 default export（需全项目扫描）。

---

## 改动清单模板（复制使用）

```markdown
## 批次：[域名/文件名]

| # | 文件:行 | 原兼容逻辑 | 删除原因 | 改动后逻辑 | 风险 |
|---|---------|-----------|---------|-----------|------|
| 1 | services/adapters/listAdapter.js:14 | `result.items` 兜底 | 后端已统一 `{data,pagination}` | 仅读 `result.data` | 🟡 需确认无旧环境 |
| 2 | services/creation.js:88 | 旧 URL `/api/tasks/` | 路由已迁移 fusion | 仅用 `/api/creation/fusion/` | 🟢 |
| 3 | pages/Works/index.jsx:42 | 本地判断 `res.items` | 已由 adapter 统一 | 使用 `result.items`（adapter 输出） | 🟡 分页绑定 |

### 修改顺序
1. listAdapter → 2. works.js → 3. Works 页面

### 验证
- [ ] `npm run build`
- [ ] 作品列表翻页 total/page 正确
- [ ] 创作提交返回 project_id 可进入工作台
```

---

## 分域批次建议

| 批次 | 范围 | 前置依赖 |
|------|------|---------|
| A | `http.js` + `listAdapter.js` | 确认全局列表接口均已 `{data,pagination}` |
| B | `businessAdapters.js` + `creation.js` + creation 页面 | A 完成 |
| C | `works.js` + works 相关页面 | A 完成 |
| D | `orders.js` + `membership.js` + `billing.js` | A 完成 |
| E | `api.js`、`admin/index.js` 别名 + 全项目 import 替换 | B–D 完成 |
| F | 全局 rg 扫尾：散落 `items`/`task_id`/legacy 注释 | E 完成 |

用户分批粘贴代码时，映射到上表批次，避免跨批重复改同一文件。

---

## 删后统一规范（批次末输出）

### 列表接口

- **请求**：`page`、`page_size`（`buildListParams` 或等价封装）。
- **响应**：拦截器解包后 adapter 只接受 `{ data: T[], pagination }`。
- **页面**：消费 adapter 输出的 `{ items, pagination }`；禁止页面再解析原始 response。

### 非列表接口

- **成功**：`code === 0`，业务数据在 `data`；错误走统一 `ApiError`。
- **字段**：与 backend Serializer 一致；前端 adapter 只做展示层衍生（格式化日期、枚举文案），不做旧字段兜底。

### 路由

- 创作：`/api/creation/fusion/*`、`/api/creation/agents/catalog/*`。
- 禁止 service 内保留旧路径常量；删除未使用的 `LEGACY_*` 常量。

### 导出

- 模块具名 export 从实现文件直接 import；`api.js` 仅保留稳定聚合（可选），不新增 `as` 别名。
- 新代码禁止 `import api from '@/services/api'` 的 default 聚合模式（若项目决定移除 default）。

### 注释

- 删除 `// 兼容旧版`、`// TODO 过渡期`；不新增「兼容新版/旧版」双轨注释。

---

## Git 与回滚

```
main
 └── chore/remove-legacy-compat
      ├── chore/compat/http-list-adapter
      ├── chore/compat/creation
      ├── chore/compat/works-orders-membership
      └── chore/compat/export-aliases
```

- Commit 示例：`refactor(api): remove legacy items branch in listAdapter`
- 单域验证失败：`git revert <commit>`，不要在同一分支 mix 多个未验证域。
- PR 描述必须附改动清单表 + 验证勾选。

---

## 风险等级

| 等级 | 场景 | 处理 |
|------|------|------|
| 🟢 | 仅删注释/死分支，rg 零引用 | 直接删 |
| 🟡 | 改 adapter 输出或删 export 别名 | 必须 rg + build |
| 🔴 | 页面内联双结构 + 分页 state 耦合 | 先改 service/adapter，再改页面，分批 PR |

---

## 与 fullstack-api-alignment 的衔接

| 阶段 | 技能 |
|------|------|
| 前端 v1 对齐新版后端 | fullstack-api-alignment（加兼容） |
| 过渡完成、后端无旧接口 | **本技能（删兼容）** |
| 删完后的目录/死文件 | fullstack-cleanup-audit |

对齐阶段写入的 `TODO 移除`、双分支 adapter，在本技能中按清单逐项删除，勿再叠加第三套写法。

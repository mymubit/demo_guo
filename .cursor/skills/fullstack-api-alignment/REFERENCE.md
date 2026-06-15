# 前端 v1.0 对齐新版后端 — 完整参考

## 一、差异梳理思路

### 1.1 比对数据源（按优先级）

| 优先级 | 后端来源 | 用途 |
|--------|----------|------|
| P0 | `config/urls.py` + `apps/*/urls.py` | 权威 URL 与方法 |
| P0 | ViewSet / APIView + Serializer | 入参、出参字段 |
| P1 | `models.py` TextChoices / IntegerChoices | 枚举值 |
| P1 | DRF exception handler / 错误码常量 | 业务错误码 |
| P2 | OpenAPI/Swagger（`drf-spectacular` 等） | 批量导出契约 |
| P2 | `tests/test_api_*.py` | 真实请求/响应样例 |

| 优先级 | 前端来源 | 用途 |
|--------|----------|------|
| P0 | `services/http.js`（或等价请求封装） | 全局解包、鉴权、错误处理 |
| P0 | `services/*.js`、`src/api/*.ts` | 各业务接口 URL 与 params |
| P1 | `services/adapters/` | 已有字段映射规则 |
| P1 | `services/constants/` | 枚举、错误码、分页默认值 |
| P2 | 页面/组件内直连 `request()` 的散落调用 | 漏网之鱼 |

### 1.2 批量排查方法

**A. 前端接口清单导出**

```bash
# 在 frontend 目录执行：提取 request 调用中的 path
rg "request\(\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]\s*,\s*['\`]" src/services src/api -n
rg "axios\.(get|post|put|patch|delete)\(" src -n
```

**B. 后端路由清单导出**

```bash
# 在 backend 目录执行
rg "path\(|router\.register\(" apps config -n --glob "*.py"
```

**C. 交叉比对**

将两端清单合并为差异总表（见 1.3）。重点关注：

- 前缀是否统一为 `/api/v1/`（或项目实际前缀）
- 资源名单复数、嵌套路径层级
- `GET` 列表 vs `POST` 搜索类接口
- 蛇形 `page_size` vs 驼峰 `pageSize`
- 响应是 `data.results` 还是 `data` 数组 + 顶层 `pagination`
- 错误是 HTTP 状态码还是 body 内 `code`

**D. 运行时抓包（开发环境）**

1. 打开浏览器 DevTools → Network，走一遍核心业务流程。
2. 记录 4xx/5xx 请求的 Request URL、Query、Body、Response。
3. 与后端 Serializer 字段对照，标注「前端多传 / 少传 / 名错 / 类型错」。

### 1.3 差异总表模板

| 模块 | 前端现状 URL | 后端现行 URL | 方法 | 入参差异 | 响应差异 | 分页差异 | 错误码差异 | 枚举差异 | 鉴权差异 | 风险 | 改造层 |
|------|-------------|-------------|------|----------|----------|----------|------------|----------|----------|------|--------|
| works 列表 | `/api/works/` | `/api/v1/works/` | GET | `status` 枚举值旧 | `count`→`total` | 无 `pagination` 顶层 | — | `draft`→`pending` | 无 | 中 | adapter + service |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

风险等级：🟢 仅字段重命名（adapter 可解）｜🟡 URL/分页结构变更｜🔴 业务流程或鉴权机制变更（需产品确认）

---

## 二、全局底层适配改造方案

> 目标：一次性改好，所有业务接口自动受益。改动集中在 `services/http.js`（或项目等价文件）及紧邻工具。

### 2.1 统一响应解包（axios 响应拦截）

**新版后端约定（对齐 fullstack-refactor-plan）：**

```json
// 成功
{ "code": 0, "message": "success", "data": {} }

// 分页成功（两种常见形态，以项目后端实际为准）
{ "code": 0, "message": "success", "data": [], "pagination": { "total": 100, "page": 1, "page_size": 20, "total_pages": 5 } }
// 或
{ "code": 0, "message": "success", "data": { "count": 100, "page": 1, "page_size": 20, "results": [] } }
```

**拦截器改造要点：**

```javascript
// parseResponse 核心逻辑（示意）
async function parseResponse(raw, config) {
  if (config?.rawResponse) return raw
  if (!raw || typeof raw !== 'object') return raw

  // 新版：以 body.code === 0 为业务成功
  if (typeof raw.code === 'number') {
    if (raw.code === API_SUCCESS_CODE) {
      // 形态 A：data + 顶层 pagination
      if (raw.pagination != null) {
        return { data: raw.data, pagination: raw.pagination }
      }
      // 形态 B：data 内嵌分页（需在 adapter 二次处理）
      return raw.data
    }
    // 业务错误：抛出自定义 ApiError，保留 code / data / message
    throw createApiError({ message: raw.message, code: raw.code, data: raw.data })
  }

  // 兼容旧版：无 code 字段时按 HTTP 200 直接返回（过渡期保留，标注 TODO 移除）
  return raw
}
```

**改造检查项：**

- [ ] `API_SUCCESS_CODE` 与后端一致（通常为 `0`）
- [ ] 同时支持「顶层 pagination」与「data 内嵌分页」两种返回
- [ ] `rawResponse: true` 保留给文件下载、第三方回调等特殊接口
- [ ] 不再在业务 service 内重复 `if (res.code === 0)`

### 2.2 全局分页与通用请求参数

**统一分页查询参数（请求侧）：**

```javascript
// services/constants/businessEnums.js
export const DEFAULT_PAGE = 1
export const DEFAULT_PAGE_SIZE = 20

// 列表请求统一构造
export function buildListParams({ page, pageSize, ordering, q, filters = {} } = {}) {
  return {
    page: page ?? DEFAULT_PAGE,
    page_size: pageSize ?? DEFAULT_PAGE_SIZE,
    ordering: ordering || undefined,
    q: q || undefined,
    ...Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    ),
  }
}
```

**统一分页解析（响应侧）— 复用 listAdapter：**

```javascript
// services/adapters/listAdapter.js
export function normalizePagination(raw, fallback = {}) {
  const source = raw && typeof raw === 'object' ? raw : {}
  return {
    total: Number(source.total ?? source.count ?? fallback.total ?? 0),
    page: Number(source.page ?? fallback.page ?? DEFAULT_PAGE),
    page_size: Number(source.page_size ?? source.pageSize ?? fallback.page_size ?? DEFAULT_PAGE_SIZE),
    total_pages: Number(source.total_pages ?? source.totalPages ?? fallback.total_pages ?? 1),
  }
}

export function normalizeListResult(result, itemMapper = (item) => item) {
  // 兼容：result 为 { data, pagination } 或 { results, count, page, page_size }
  const items = Array.isArray(result?.data)
    ? result.data
    : Array.isArray(result?.results)
      ? result.results
      : []
  const paginationSource = result?.pagination ?? result
  return {
    items: items.map(itemMapper).filter(Boolean),
    pagination: normalizePagination(paginationSource),
    facets: result?.facets,
    meta: result?.meta,
  }
}
```

**页面层约定：** 列表页只消费 `{ items, pagination }`，禁止直接读 `res.count` / `res.results`。

### 2.3 全局错误码与 Sonner 提示

**错误码常量对齐：**

```javascript
// services/constants/errorCodes.js — 与后端分层一致
export const API_SUCCESS_CODE = 0

export const API_ERROR_CODES = {
  VALIDATION_ERROR: 4001,    // 参数校验
  UNAUTHORIZED: 401,
  TOKEN_EXPIRED: 4011,
  PERMISSION_DENIED: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 42901,
  SERVER_ERROR: 500,
}

export const AUTH_ERROR_CODES = new Set([401, 4011])
export const PERMISSION_ERROR_CODES = new Set([403])
export const RATE_LIMIT_ERROR_CODES = new Set([42901])
```

**Sonner 统一报错（页面 / Hook 层）：**

```javascript
import { toast } from 'sonner'
import { formatUserError } from '@/utils/userError'

export function handleApiError(error, { silent = false, fieldHandler } = {}) {
  if (silent) return

  // 表单字段错误：交给 useFormErrors
  if (fieldHandler && error?.data?.field_errors) {
    fieldHandler(error.data.field_errors)
    return
  }

  // 鉴权/权限：http 拦截器已处理跳转，页面层可静默
  if (error?.isAuthError || error?.isPermissionError) return

  toast.error(formatUserError(error?.message, '操作失败，请稍后重试'))
}
```

**拦截器 vs 页面分工：**

| 场景 | 处理位置 |
|------|----------|
| 401 Token 过期 + 刷新 | `http.js` 拦截器 |
| 403 无权限 | 拦截器标记 `isPermissionError`，路由守卫或页面决定是否 toast |
| 429 限流 | 拦截器附加 `reset_after` 文案 |
| 表单字段校验 4001 | 页面 `useFormErrors` + `field_errors` |
| 普通业务错误 | 页面 `catch` 中 `handleApiError` |

### 2.4 全局鉴权与 Token

**对齐检查项：**

- [ ] Header 格式：`Authorization: Bearer <access>`
- [ ] Refresh 路径与 body：`POST /api/auth/refresh/`，`{ refresh: "<token>" }`
- [ ] 响应字段：`access` / `refresh`（而非旧版 `token`）
- [ ] 存储键与 zustand persist 格式兼容（`readPersistedAuthState` 多字段兜底）
- [ ] 管理端与用户端登录失效跳转路径分离（`/admin/login` vs `/login`）
- [ ] 签名头（如 `X-Signature`）：仅在后端启用时保留，与新版鉴权文档一致
- [ ] `withCredentials` / CORS：前端不擅自改，跨域问题在后端 `CORS_ALLOWED_ORIGINS` 修

---

## 三、分层迭代改造执行步骤

### 步骤1：底层请求工具全局适配 + 基础连通性自测

**改动范围：** `services/http.js`、`services/admin/http.js`（如有）、`errorCodes.js`

**Checklist：**

- [ ] 响应解包支持新版 `{ code, message, data }`
- [ ] 分页两种形态均可透传
- [ ] 401 自动 refresh + 重试一次
- [ ] 429 / 403 / 业务错误码正确抛出 `ApiError`
- [ ] `request()` 签名与现有业务 service 兼容

**冒烟验证：**

```
- [ ] GET /api/health 或等价探活接口 → code === 0
- [ ] 未登录访问受保护接口 → 跳转登录页
- [ ] 登录后携带 Bearer → 200 + 正确 data
- [ ] 故意传错参数 → 收到 4001 + field_errors
- [ ] Token 过期 → 自动 refresh 或跳转登录
```

**回滚点：** `git revert` 步骤1 的单个 commit；业务 service 无需改动。

---

### 步骤2：公共枚举、常量、类型定义对齐

**改动范围：** `services/constants/businessEnums.js`、`types/`（如有 TS）

**方法：**

1. 从后端 `TextChoices` 导出枚举表，与前端常量 diff。
2. 保留 UI 展示映射（`UI_XXX_TO_API_XXX`），UI 文案不变，只改映射目标值。
3. 删除前端已无后端对应的废弃枚举，标注 `@deprecated` 过渡期常量。

**示例 — 状态枚举对齐：**

```javascript
// 后端 ProjectStatus.PENDING = 'pending'
export const PROJECT_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
}

// UI Tab 值 → API 查询参数（页面 Tab key 不变）
export const UI_WORK_STATUS_TO_API_STATUS = {
  all: undefined,
  draft: PROJECT_STATUS.PENDING,      // 旧版可能为 'draft'
  generating: PROJECT_STATUS.RUNNING,
}
```

**完成判定：** 所有 service 引用的枚举在差异总表中无 🔴 未处理项。

---

### 步骤3：业务接口文件批量改造

**改动范围：** `services/{domain}.js` 或 `src/api/{domain}.ts`（不改页面）

**标准改造模板：**

```javascript
// ===== 改造前（v1.0 典型问题）=====
async list(page) {
  const res = await request('GET', '/api/works', { params: { page, limit: 12 } })
  return {
    list: res.results || res.data?.list || [],
    total: res.count || res.total,
  }
}

// ===== 改造后 =====
import { buildListParams } from './utils/listParams'       // 或内联
import { normalizeListResult } from './adapters/listAdapter'
import { normalizeWorkItem } from './adapters/businessAdapters'
import { UI_WORK_STATUS_TO_API_STATUS } from './constants/businessEnums'

async list(page, status, pageSize = 12, options = {}) {
  const apiStatus = UI_WORK_STATUS_TO_API_STATUS[status] ?? status
  const data = await request('GET', '/api/v1/works/', {
    params: buildListParams({
      page,
      pageSize,
      filters: { status: apiStatus && apiStatus !== 'all' ? apiStatus : undefined },
      q: options.q,
      ordering: options.ordering,
    }),
  })
  const result = normalizeListResult(data, normalizeWorkItem)
  return { items: result.items, pagination: result.pagination }
}
```

**详情接口 — adapter 隔离字段变更：**

```javascript
// adapters/businessAdapters.js
export function normalizeWorkDetail(raw) {
  if (!raw || typeof raw !== 'object') return null
  return {
    id: raw.id,
    title: raw.title ?? raw.name,           // 字段重命名
    status: raw.status,
    statusText: CREATION_STATUS_TEXT[raw.status] ?? raw.status,
    createdAt: raw.created_at ?? raw.createdAt,
    updatedAt: raw.updated_at ?? raw.updatedAt,
    // 嵌套结构拍平
    authorName: raw.author?.display_name ?? raw.author_name ?? '',
  }
}
```

**改造顺序建议（按依赖与流量）：**

1. `auth.js` — 登录态是一切前提
2. 首页/仪表盘只读接口
3. 核心业务 CRUD（works、creation、orders）
4. 管理端 `services/admin/`
5. 低频工具类接口

**每模块完成判定：** 该模块所有接口在差异总表标记为「已对齐」，Network 无 404/字段 undefined 连锁错误。

---

### 步骤4：页面与组件数据取值修正

> 原则：能不改则不改；必须改时只改数据绑定表达式，不动 JSX 结构。

**典型修复模式：**

```jsx
// 改造前
const { list, total } = await works.list(page)
setItems(list)
setTotal(total)

// 改造后 — 若步骤3 已返回统一结构，页面可零改动
// 若步骤3 暂未统一，页面最小改动：
const { items, pagination } = await works.list(page, status, pageSize)
setItems(items)
setTotal(pagination.total)
```

```jsx
// 枚举显示 — 优先用 adapter 已附带的 statusText，避免页面改映射
<span>{item.statusText ?? CREATION_STATUS_TEXT[item.status]}</span>
```

**排查命令：**

```bash
rg "\.results|\.count|\.list\b|res\.data\.data" src/pages src/components -n
rg "pageSize|page_size|limit" src/pages -n
```

**完成判定：** 控制台无 `Cannot read properties of undefined`；列表分页翻页正常；表单提交错误能落到字段级提示。

---

### 步骤5：全流程功能回归测试

**回归矩阵：**

| 域 | 用例 | 验证点 |
|----|------|--------|
| 鉴权 | 登录 / 登出 / 过期刷新 | Token 写入、跳转、重试 |
| 列表 | 筛选 / 排序 / 翻页 | `items` 数量、`pagination.total` |
| 详情 | 打开 / 刷新 | 字段完整渲染 |
| 表单 | 创建 / 编辑 / 校验失败 | field_errors、Sonner |
| 删除 | 软删 / 硬删 | 列表刷新 |
| 管理端 | 权限边界 | 403 处理 |
| 文件 | 导出 / 上传 | `rawResponse` / `blob` |

**自动化（可选）：**

- 后端：`pytest apps/xxx/tests/test_api_*.py` 作为契约基准
- 前端：对 `adapters/` 写单元测试（输入旧/新后端 JSON，断言统一输出）
- E2E：仅覆盖 3–5 条黄金路径，不在对齐 PR 中大规模新增

**发布前检查：**

- [ ] 差异总表全部关闭或标注已知限制
- [ ] `npm run build` 通过
- [ ] 无新增 `console.log` 调试残留
- [ ] `.env.example` 中 `VITE_API_BASE_URL` 与后端一致

---

## 四、Git 分支管理策略

### 4.1 分支模型

```text
main                          # 生产基线
└── feat/api-alignment        # 对齐总集成分支（可选）
    ├── feat/api-alignment/01-http-base
    ├── feat/api-alignment/02-enums
    ├── feat/api-alignment/03-works
    ├── feat/api-alignment/04-creation
    └── feat/api-alignment/05-admin
```

### 4.2 Commit 规范

```
fix(api): align http response unwrap with backend v2 envelope
fix(api): sync PROJECT_STATUS enum with backend TextChoices
fix(api): migrate works list to /api/v1/works/ and normalize pagination
fix(pages): read pagination.total in Works list page
```

### 4.3 分批合并策略

1. **步骤1（http-base）** 单独 PR，优先合并；冲突面最小。
2. **步骤2（enums）** 可与步骤1 同 PR，若枚举量大则拆分。
3. **步骤3+4** 按业务域一个 PR 一个域；每个 PR < 500 行 diff 为宜。
4. 每个 PR 附：差异总表截图（该域行）、冒烟清单勾选、回滚命令。

### 4.4 回滚

```bash
# 回滚最近一次错误 commit
git revert HEAD

# 回滚整个域的合并（假设 merge commit 为 abc1234）
git revert -m 1 abc1234

# 步骤1 回滚后：业务 service 仍兼容旧拦截器行为（过渡期双支持）
```

### 4.5 禁止事项

- 禁止在 `feat/api-alignment` 上 force push 已共享分支
- 禁止一个 PR 同时含 API 对齐 + UI 改版 + 清理废弃文件
- 禁止未跑 build 就合并

---

## 五、配套编码约束与常态化机制

### 5.1 接口对接规范（改造完成后生效）

**后端：**

- 所有对外接口路径统一 `/api/v1/{resource}/`
- 响应统一 `{ code, message, data }`；分页字段命名固定 `total/page/page_size/total_pages`
- 枚举使用 `TextChoices`，文档或 OpenAPI 中可查阅
- 破坏性变更必须升版本或提供过渡期双写，禁止静默删字段

**前端：**

- 禁止页面直接 `fetch` / 裸 `axios`；统一走 `request()`
- 禁止页面拼接 URL；URL 只在 `services/{domain}.js` 定义
- 字段映射集中在 `adapters/`，禁止在 JSX 写 `item.foo_bar || item.fooBar || ''` 超过一层
- 枚举查询使用 `UI_*_TO_API_*` 映射，展示使用 `*_STATUS_TEXT`
- 错误处理：拦截器管鉴权/限流，页面管业务 toast 和表单字段

### 5.2 接口同步常态化机制

| 机制 | 频率 | 负责人 | 动作 |
|------|------|--------|------|
| 契约 Diff | 每个后端 API PR | 后端 | PR 模板勾选「是否破坏性变更」 |
| 前端差异扫描 | 每周或发版前 | 前端 | 运行 `rg request\(` 清单 vs 后端 urls |
| Adapter 单测 | 枚举/字段变更时 | 前端 | 新增后端样例 JSON fixture |
| 联调冒烟 | 发版前 | 双方 | 过一遍回归矩阵黄金路径 |
| OpenAPI 导出 | 后端发版 | 后端 | 导出 yaml 存 `docs/openapi.yaml`，前端 diff |

**PR 模板片段（建议加入 `.github/pull_request_template.md`）：**

```markdown
## API 变更（后端 PR 必填）
- [ ] 无破坏性变更
- [ ] 有破坏性变更（说明迁移方式、过渡期）
  - 变更类型：URL / 入参 / 出参 / 枚举 / 鉴权 / 错误码
  - 影响前端文件：...
  - 前端对齐 Issue/PR：...
```

### 5.3 发现后端问题时的处理

对齐过程中若发现后端 bug 或契约矛盾：

1. 在前端用最小兼容 shim（adapter 兜底），标注 `// TODO(backend): issue #xxx`
2. 单独开后端 Issue/PR，不在对齐分支改后端逻辑
3. 差异总表增加「待后端确认」列，不阻塞其他域推进

---

## 六、快速决策表

| 症状 | 优先改造层 | 是否改页面 |
|------|-----------|-----------|
| 全站 401 / 解包失败 | `http.js` | 否 |
| 仅某列表分页错乱 | `listAdapter` + 对应 service | 可能（total 字段名） |
| 某字段 undefined | `businessAdapters` | 否（优先） |
| 枚举显示英文/raw 值 | `businessEnums` 映射 | 否 |
| 表单校验不显示 | `useFormErrors` + error `field_errors` | 是（错误绑定） |
| 404 Not Found | service URL 路径 | 否 |

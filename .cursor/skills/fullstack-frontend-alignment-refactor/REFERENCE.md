# 前端 v1.0 结构性重构 + 对齐新版后端 — 完整参考

## 一、差异清单模板

### 1.1 比对数据源

| 优先级 | 后端来源 | 用途 |
|--------|----------|------|
| P0 | `config/urls.py` + `apps/*/urls.py` | 权威 URL 与方法 |
| P0 | ViewSet / APIView + Serializer | 入参、出参字段 |
| P1 | `models.py` TextChoices | 枚举值 |
| P1 | exception handler / 错误码常量 | 业务错误码 |
| P2 | OpenAPI/Swagger | 批量导出契约 |
| P2 | `tests/test_api_*.py` | 真实请求/响应样例 |

| 优先级 | 前端来源 | 用途 |
|--------|----------|------|
| P0 | `services/http.js` 或 `api/client.ts` | 全局解包、鉴权 |
| P0 | `services/*.js`、`src/api/modules/` | 业务 URL 与 params |
| P1 | `adapters/` | 已有字段映射 |
| P1 | `constants/`、`types/` | 枚举、错误码 |
| P2 | 页面内散落 `request()` | 漏网之鱼，需收敛到 api 层 |

### 1.2 批量排查命令

```bash
# 前端：提取接口调用
rg "request\(\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]" src/services src/api src/pages -n
rg "axios\.(get|post|put|patch|delete)\(" src -n

# 后端：路由清单
rg "path\(|router\.register\(" apps config -n --glob "*.py"

# 前端：散落解析逻辑（需收敛）
rg "\.results|\.count|res\.data\.data|pageSize|page_size" src/pages src/components -n

# 基础组件目录（标记为只读，改造时跳过）
rg -l "from '@/components/ui" src | head -20
```

### 1.3 差异总表

| 模块 | 前端现状 URL | 后端现行 URL | 方法 | 入参差异 | 响应差异 | 分页差异 | 错误码 | 枚举 | 鉴权 | 散落调用位置 | 风险 | 改造层 |
|------|-------------|-------------|------|----------|----------|----------|--------|------|------|-------------|------|--------|
| works 列表 | `/api/works` | `/api/v1/works/` | GET | `limit`→`page_size` | `count`→`total` | 嵌套层级变更 | — | `draft`→`pending` | — | `pages/Works/index.jsx:45` | 🟡 | adapter + api module + hook |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

风险：🟢 字段重命名｜🟡 URL/分页/结构变更｜🔴 鉴权或业务流程变更

### 1.4 结构性问题登记表（本技能特有）

| 问题类型 | 现状描述 | 目标改法 | 涉及文件 | 是否动 ui 组件 |
|----------|----------|----------|----------|----------------|
| 重复请求 | 列表页 mount 两次 fetch | 合并为 `useWorksList` hook | `pages/Works/index.jsx` | 否 |
| 散落 URL | 页面内直接 `request('GET','/api/...')` | 迁入 `api/modules/works.ts` | 多处 | 否 |
| 状态冗余 | 全局 store 与页面 state 双写 | 服务端状态进 hook，删冗余 store | `store/` + 页面 | 否 |
| 解析重复 | 5 处 `res.results \|\| res.data` | 统一 `normalizeListResult` | adapters | 否 |

---

## 二、底层架构结构性重塑

### 2.1 Axios 客户端分层

**目标文件：** `src/api/client.ts`（或重构现有 `services/http.js`）

```typescript
// client.ts — 职责：实例、拦截器、错误类型，不含业务 URL
import axios from 'axios'
import { toast } from 'sonner'
import { API_SUCCESS_CODE, AUTH_ERROR_CODES } from './constants/errorCodes'
import { refreshAccessToken, clearAuthAndRedirect } from './modules/auth'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (response) => {
    const raw = response.data
    if (response.config.rawResponse) return raw
    if (typeof raw?.code === 'number') {
      if (raw.code === API_SUCCESS_CODE) {
        if (raw.pagination != null) return { data: raw.data, pagination: raw.pagination }
        return raw.data
      }
      throw createApiError(raw)
    }
    return raw // 过渡期兼容无 code 的旧响应
  },
  async (error) => {
    if (isTokenExpired(error)) {
      const ok = await refreshAccessToken()
      if (ok) return client.request(error.config)
      clearAuthAndRedirect()
      return Promise.reject(error)
    }
    if (!error.config?.silent) handleGlobalError(error)
    return Promise.reject(error)
  }
)

export function request<T>(method: string, url: string, options = {}) {
  return client.request<T>({ method, url, ...options })
}
```

**检查项：**

- [ ] 业务 URL 不在 client 内硬编码
- [ ] `{ code, message, data }` 与分页两种形态均支持
- [ ] 401 refresh + 单次重试
- [ ] Sonner 仅在非 silent、非鉴权场景弹出
- [ ] `rawResponse` 保留给 blob/文件下载

### 2.2 API 模块目录重构

**迁移原则：**

1. 一个业务域一个文件：`api/modules/{domain}.ts`
2. 页面/组件禁止新增裸 `request()`；旧调用逐步迁入 module
3. module 只负责：URL、params 构造、调用 adapter、返回前端统一形状
4. 不改 module 消费者的 JSX 结构，只改 import 路径与返回值字段名

**改造前（散乱）：**

```javascript
// pages/Works/index.jsx 内
const res = await request('GET', '/api/works', { params: { page, limit: 12, status } })
setItems(res.results || res.data?.list || [])
setTotal(res.count ?? res.total ?? 0)
```

**改造后（分层）：**

```typescript
// api/modules/works.ts
import { request } from '../client'
import { buildListParams } from '../utils/listParams'
import { normalizeListResult } from '../adapters/listAdapter'
import { normalizeWorkItem } from '../adapters/workAdapter'
import { UI_WORK_STATUS_TO_API_STATUS } from '../constants/businessEnums'

export async function fetchWorksList(params: WorksListParams) {
  const apiStatus = UI_WORK_STATUS_TO_API_STATUS[params.status] ?? params.status
  const data = await request('GET', '/api/v1/works/', {
    params: buildListParams({
      page: params.page,
      pageSize: params.pageSize,
      filters: { status: apiStatus !== 'all' ? apiStatus : undefined },
      q: params.q,
    }),
  })
  return normalizeListResult(data, normalizeWorkItem)
}

// hooks/useWorksList.ts
export function useWorksList(initialParams: WorksListParams) {
  const [params, setParams] = useState(initialParams)
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['works', params],
    queryFn: () => fetchWorksList(params),
  })
  return { items: data?.items ?? [], pagination: data?.pagination, isLoading, error, setParams, refetch }
}

// pages/Works/index.jsx — JSX 结构不变，只换数据来源
const { items, pagination, isLoading, setParams } = useWorksList({ page: 1, pageSize: 12, status: 'all' })
```

### 2.3 常量、枚举、类型对齐

```typescript
// api/constants/businessEnums.ts — 与后端 TextChoices 一一对应
export const PROJECT_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

// UI Tab key 不变，只改映射目标（对齐后端）
export const UI_WORK_STATUS_TO_API_STATUS: Record<string, string | undefined> = {
  all: undefined,
  draft: PROJECT_STATUS.PENDING,
  generating: PROJECT_STATUS.RUNNING,
}

// api/types/works.ts
export interface WorksListParams {
  page: number
  pageSize: number
  status?: string
  q?: string
}

export interface WorkItem {
  id: string
  title: string
  status: string
  statusText: string
  createdAt: string
}
```

**废弃常量处理：** 标注 `@deprecated`，保留一个迭代周期后删除；差异总表登记。

### 2.4 鉴权与 Token 刷新

检查项：

- [ ] Header：`Authorization: Bearer <access>`
- [ ] Refresh：`POST /api/v1/auth/refresh/`，body `{ refresh }`
- [ ] 响应字段 `access` / `refresh`（非旧版 `token`）
- [ ] 存储键与 persist 格式兼容
- [ ] 用户端/管理端登录失效跳转路径分离
- [ ] 权限判断与后端 Permission 类一致，不在页面硬编码 role 字符串

---

## 三、业务层改造示例

### 3.1 清理冗余 useEffect + 重复请求

**改造前：**

```jsx
useEffect(() => { loadList() }, [])
useEffect(() => { if (status) loadList() }, [status, page])

async function loadList() {
  setLoading(true)
  const res = await request('GET', '/api/works', { params: { page, status } })
  setItems(res.results)
  setLoading(false)
}
```

**改造后：**

```jsx
// 合并为单一数据源；依赖由 hook/query 管理
const { items, pagination, isLoading, setParams } = useWorksList({ page, pageSize: 12, status })

useEffect(() => {
  setParams((p) => ({ ...p, page, status }))
}, [page, status, setParams])
```

**重构理由：** 消除双 effect 竞态；URL/params 变更集中在 api module。

### 3.2 Adapter 隔离字段变更（页面零改动优先）

```typescript
// api/adapters/workAdapter.ts
export function normalizeWorkItem(raw: Record<string, unknown>): WorkItem | null {
  if (!raw?.id) return null
  return {
    id: String(raw.id),
    title: String(raw.title ?? raw.name ?? ''),
    status: String(raw.status ?? ''),
    statusText: CREATION_STATUS_TEXT[raw.status as string] ?? String(raw.status),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
  }
}
```

**适配改动点：** `name`→`title`、`created_at` 蛇形、枚举 raw 值→展示文案。

### 3.3 状态管理精简

**改造前：** 列表数据同时存 Zustand + 组件 state，刷新不同步。

**改造后：**

- 服务端列表/详情 → React Query / SWR / 自定义 hook（单一来源）
- Zustand 仅保留：用户信息、全局 UI 开关、跨页面临时草稿
- 删除与接口数据重复的 store slice

```typescript
// 反模式：禁止
useEffect(() => {
  worksStore.setList(items) // 与 hook 双写
}, [items])
```

### 3.4 基础公共组件调用约束

```jsx
// ✅ 允许：业务层改传入 props 的值
<Button onClick={handleSubmit} disabled={isSubmitting}>提交</Button>
<Pagination current={pagination.page} total={pagination.total} onChange={setPage} />

// ❌ 禁止：修改 @/components/ui/Button.jsx 内部实现
// ❌ 禁止：改 Button 的 props 接口签名
// ❌ 禁止：为对齐后端而改 Card 布局 className
```

### 3.5 表单错误对齐

```jsx
const { fieldErrors, setFieldErrors, clearFieldErrors } = useFormErrors()

async function handleSubmit(values) {
  clearFieldErrors()
  try {
    await updateWork(id, values)
    toast.success('保存成功')
  } catch (err) {
    if (err?.data?.field_errors) {
      setFieldErrors(err.data.field_errors)
      return
    }
    handleApiError(err)
  }
}

// 基础 Input 组件不变，只改 error 绑定字段名
<Input error={fieldErrors.title} ... />
```

---

## 四、分批次落地执行步骤

### 步骤1：Git 分支 + 备份 + 回滚策略

```bash
git checkout -b feat/frontend-alignment-refactor
git tag backup/frontend-v1.0-$(date +%Y%m%d)   # 或使用 git branch backup/frontend-v1.0
```

**交付物：**

- [ ] 改造分支与 v1.0 备份 tag/分支
- [ ] 差异总表空模板已创建（`docs/api-diff-tracker.md` 或 Issue）
- [ ] 回滚预案：逐步骤 revert，步骤2 回滚不影响已改 api module

---

### 步骤2：底层请求架构重构 + 连通性

**范围：** `api/client.ts`、`constants/errorCodes`、`modules/auth.ts`（refresh）

**冒烟：**

- [ ] 探活接口 `code === 0`
- [ ] 未登录 → 跳转登录
- [ ] 登录后 Bearer 正常
- [ ] 错参 → 业务错误码 + message
- [ ] Token 过期 → refresh 或登出

**回滚点：** 单 commit revert `feat/far/01-http`

---

### 步骤3：枚举、常量、类型对齐

**范围：** `api/constants/`、`api/types/`、废弃常量清理

**完成判定：** 差异总表枚举/错误码列无 🔴 未处理项

---

### 步骤4：API 模块批量重构

**顺序：** auth → 首页只读 → 核心 CRUD → admin → 低频工具

**每模块：**

- [ ] URL/params 对齐后端
- [ ] adapter 输出稳定前端模型
- [ ] 页面内散落 `request()` 迁入 module
- [ ] 模块 Network 无 404/422

**回滚：** 按业务域 revert，不影响其他域

---

### 步骤5：页面/组件数据解析修正（单模块）

**原则：**

- 优先通过步骤4 返回值统一，减少页面改动
- 必须改时：数据绑定、hook 引用、store 精简；不动 JSX 布局与 ui 组件
- 每模块完成后自测：列表翻页、详情字段、表单提交、错误提示

**排查：**

```bash
rg "request\(" src/pages src/components --glob "!**/ui/**" -n
```

---

### 步骤6：全流程回归 + 归档

**回归矩阵：**

| 域 | 用例 | 验证点 |
|----|------|--------|
| 鉴权 | 登录/登出/refresh | Token、跳转 |
| 列表 | 筛选/排序/翻页 | items、pagination.total |
| 详情 | 打开/刷新 | 字段完整 |
| 表单 | 创建/编辑/校验失败 | field_errors、Sonner |
| 权限 | 403 边界 | 提示/跳转 |
| 文件 | 上传/导出 | rawResponse |

**归档文档：**

- 差异总表终态（已关闭 / 已知限制 / 待后端）
- 新增/迁移的 api module 清单
- adapter 字段映射表
- 废弃常量与迁移说明

---

## 四（续）、Git 分支与回滚

```text
main
└── feat/frontend-alignment-refactor
    ├── feat/far/01-backup-and-http
    ├── feat/far/02-enums-types
    ├── feat/far/03-api-works
    ├── feat/far/04-hooks-works
    └── feat/far/05-pages-works
```

**Commit 示例：**

```
refactor(api): extract axios client and align response envelope
refactor(api): modularize works endpoints under api/modules
refactor(hooks): add useWorksList and remove duplicate useEffect fetch
fix(pages): bind Works list to normalized pagination.total
```

**禁止：**

- 同一 PR 混合 API 重构 + UI 改版 + 删文件
- 修改 `@/components/ui/**`
- 未 build 即合并

---

## 五、长期规范机制

### 5.1 前后端接口同步规范

**后端：**

- 路径统一 `/api/v1/{resource}/`
- 响应 `{ code, message, data }`；分页 `total/page/page_size/total_pages`
- 枚举用 TextChoices；破坏性变更升版本或过渡期双写
- PR 模板勾选「是否破坏性变更」

**前端：**

- 禁止页面裸 `fetch`/`axios`；统一 `api/client` + `api/modules`
- URL 只在 module 定义；字段映射只在 `adapters/`
- UI Tab/筛选项用 `UI_*_TO_API_*` 映射，展示用 `*_TEXT`
- `@/components/ui/**` 变更走独立 UI PR，不与 API 对齐混合

### 5.2 前端编码规范（防再次混乱）

| 规则 | 说明 |
|------|------|
| 数据下行 | 后端 → adapter → hook → 页面，单向流动 |
| 请求上行 | 页面 → hook/module → client，不在组件拼 params |
| 列表页 | 只消费 `{ items, pagination }` |
| 错误 | 拦截器管鉴权/限流；页面管 toast 与 field_errors |
| 状态 | 接口数据不进 Zustand（除非离线缓存明确需求） |
| 类型 | 新 module 必须带 TS 类型或 JSDoc typedef |

### 5.3 常态化机制

| 机制 | 频率 | 动作 |
|------|------|------|
| 契约 Diff | 后端 API PR | 勾选破坏性变更 |
| 前端扫描 | 发版前 | `rg request\(` vs 后端 urls |
| Adapter 单测 | 字段变更时 | fixture JSON 断言 |
| 联调冒烟 | 发版前 | 黄金路径回归 |
| OpenAPI | 后端发版 | 导出 diff |

### 5.4 后端问题处理

1. 前端 adapter 最小 shim，标注 `// TODO(backend): #issue`
2. 单独后端 Issue/PR，不在对齐分支改后端
3. 差异总表「待后端确认」列，不阻塞其他域

---

## 六、快速决策表

| 症状 | 优先改造层 | 改 ui 组件 | 改页面 JSX 结构 |
|------|-----------|-----------|----------------|
| 全站解包/401 失败 | `api/client` | 否 | 否 |
| 某列表分页错乱 | `listAdapter` + module | 否 | 否 |
| 字段 undefined | `businessAdapter` | 否 | 否 |
| 重复请求/竞态 | hook 合并 effect | 否 | 否 |
| URL 404 | `api/modules` | 否 | 否 |
| 散落 request | 迁入 module | 否 | 否 |
| 双写状态不同步 | 删 store 冗余 | 否 | 否 |
| 表单校验不显示 | `useFormErrors` | 否 | 仅 error 绑定 |

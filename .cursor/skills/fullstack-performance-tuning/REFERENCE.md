# Fullstack Performance Tuning — 详细参考

## 性能诊断报告模板

```markdown
# [模块/接口/页面] 性能诊断报告

## 一、症状与范围
- 现象：…
- 影响路由/接口：…
- 数据样本：监控时间段 / 复现条件

## 二、度量证据

| 指标 | 优化前 | 目标 | 采集方式 |
|------|--------|------|----------|
| 接口 P95 | 3200ms | <500ms | 监控 / curl |
| SQL 次数/请求 | 87 | <5 | django-debug-toolbar / 日志 |
| 首屏请求数 | 18 | <10 | Network |
| LCP | 4.2s | <2.5s | Performance |

## 三、根因分析（按优先级）

### [P0] 根因标题
**证据**：…
**影响**：…

## 四、优化方案

| # | 项 | 文件 | 改动摘要 | 预期收益 | 风险 |
|---|-----|------|----------|----------|------|
| 1 | 修 N+1 | services/works.py | prefetch_related | SQL 87→3 | 低 |

## 五、验证计划
1. …

## 六、不建议项
- …
```

---

## 后端诊断清单

### ORM 与查询

- [ ] 单请求 SQL 条数（N+1：`for x in qs: x.fk.field`）
- [ ] 是否使用 `select_related`（FK 单对象）、`prefetch_related`（M2M/反查）
- [ ] `only()` / `defer()` 是否减少 Serializer 字段拉取
- [ ] 列表是否 `values()` 过度或 Serializer 嵌套过深
- [ ] 分页：避免大 `OFFSET`；评估游标/keyset 分页
- [ ] `count()` 是否触发昂贵查询；考虑缓存 count 或近似值
- [ ] 是否存在循环内 `.save()` / `.create()` → 改 `bulk_create`/`bulk_update`

### 索引与数据库

- [ ] `filter` / `order_by` / `join` 字段是否有索引
- [ ] 复合索引顺序是否匹配查询模式
- [ ] 慢查询日志 / 监控中 Top SQL
- [ ] 全表扫描、filesort、临时表

### 缓存

- [ ] 热点只读数据是否缓存（配置、字典、首页聚合）
- [ ] cache key 命名空间与 TTL 是否合理
- [ ] 写后是否失效相关 key
- [ ] 是否缓存整个 queryset 对象（注意序列化与版本）

### 接口层

- [ ] View 内是否有同步 IO（外部 HTTP、大文件、邮件）
- [ ] 是否应下沉 Celery 异步任务
- [ ] Serializer `SerializerMethodField` 是否触发额外查询
- [ ] 响应体是否返回过大冗余字段
- [ ] throttle 是否误伤；分页 page_size 上限

---

## 后端优化模式

### N+1 修复

```python
# 反模式
for work in Work.objects.filter(user_id=uid):
    print(work.project.name)  # 每条一次 SQL

# 推荐
works = Work.objects.filter(user_id=uid).select_related("project")
```

```python
# M2M / 反向外键
qs = Order.objects.prefetch_related("items", "items__product")
```

### 索引添加（须迁移）

```python
class Meta:
    indexes = [
        models.Index(fields=["user", "-created_at"]),
        models.Index(fields=["status", "updated_at"]),
    ]
```

说明：写入略增开销；大表加索引需评估锁表窗口。

### 批量操作

```python
# 反模式：循环 save
# 推荐
Model.objects.bulk_create(items, batch_size=500)
Model.objects.bulk_update(items, ["status"], batch_size=500)
```

### 缓存读热点

```python
from django.core.cache import cache

def get_hot_config(key):
    val = cache.get(key)
    if val is None:
        val = Config.objects.get(key=key).value
        cache.set(key, val, timeout=300)
    return val
```

### 异步耗时任务

- 报表导出、批量通知、大文件处理 → Celery task
- API 立即返回 task_id，前端轮询或 WebSocket 进度

---

## 前端诊断清单

### 网络

- [ ] 同一接口是否重复调用（Strict Mode 双 mount、useEffect 缺依赖）
- [ ] 是否可并行却串行（await 链）
- [ ] 列表+详情是否重复拉全量
- [ ] 是否缺少请求去抖/节流（搜索框）
- [ ] 是否未取消过期请求（竞态）

### 渲染

- [ ] 大列表（>100 行）是否虚拟滚动
- [ ] 父组件 state 变化导致整树重渲染
- [ ] 内联对象/函数作为 props 破坏 memo
- [ ] ECharts 是否在不可见时仍 resize/更新
- [ ] framer-motion 列表 stagger 过大

### 加载与构建

- [ ] 路由是否 `React.lazy` + `Suspense`
- [ ] 是否整包引入 lodash/echarts → 按需导入
- [ ] 图片是否过大、未懒加载
- [ ] 首屏是否加载非必要 admin/图表 chunk

---

## 前端优化模式

### 合并与去重请求（React Query 示例）

若项目已用 React Query，优先 `staleTime`、`queryKey` 去重；未用时：

```tsx
// 反模式：父子各 fetch 同一 user
// 推荐：提升 fetch 到 layout 或 useQuery 共享 key
```

### useEffect 请求规范

```tsx
useEffect(() => {
  const controller = new AbortController();
  fetchList({ signal: controller.signal });
  return () => controller.abort();
}, [page, filters]); // 依赖完整，避免漏依赖重复请求
```

### 大列表虚拟化

- 表格/列表超过 100 条评估 `@tanstack/react-virtual` 或项目已有虚拟列表组件
- 禁止用数组 index 作 key 导致全量重排

### 路由懒加载

```tsx
const WorksPage = lazy(() => import("./pages/WorksPage"));
```

### memo 使用边界

仅对 Profiler 证实的热点子组件使用 `memo`/`useMemo`/`useCallback`，禁止全量包裹。

---

## 压测与对比要点

### 简易后端压测

```bash
# ab（单接口）
ab -n 200 -c 10 -H "Authorization: Bearer TOKEN" https://api.example.com/api/v1/works/

# 关注：Requests per second、Time per request、Failed requests
```

或使用 k6/locust 做阶梯并发，记录 P50/P95/P99。

### 对比原则

- 固定数据量与环境（预发）
- 优化前后同参数、同并发
- 同时看延迟与错误率，不单看均值
- ORM 优化后对比 SQL 条数（`assertNumQueries` / debug toolbar）

### Django 测试断言查询数

```python
with self.assertNumQueries(3):
    response = self.client.get("/api/v1/works/")
    self.assertEqual(response.status_code, 200)
```

---

## 常见反模式对照

| 反模式 | 后果 | 修复方向 |
|--------|------|----------|
| Serializer 嵌套 3 层+ | N+1、响应巨大 | 扁平 DTO、prefetch |
| 列表接口无分页 | 内存/传输爆炸 | 强制 StandardPagination |
| 每次请求算聚合 | CPU 热点 | 缓存/物化视图/定时汇总 |
| 前端每次 render fetch | 请求风暴 | 稳定依赖 + 请求锁 |
| 深分页 page=5000 | DB 慢 | 游标分页 |
| 缓存永不过期 | 脏读 | TTL + 写失效 |

---

## 与监控技能联动

若已接入 `fullstack-monitoring-system`：

1. 从监控后台导出慢接口 Top N、慢 SQL 样本
2. 优化后在同一时间段对比 P95
3. 对关键路径添加自定义 `trackEvent('perf_works_list', { duration_ms })` 做前后对比

---

## 验证检查表（优化后）

- [ ] 核心功能回归通过（链接 testing P0 用例）
- [ ] 目标接口 P95 下降 ≥30% 或达目标值
- [ ] SQL 条数/请求数降至预期
- [ ] 无新增缓存一致性问题
- [ ] 索引迁移已在预发验证
- [ ] 前端无新增重复请求（Network 抽查）

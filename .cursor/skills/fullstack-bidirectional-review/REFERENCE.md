# Fullstack Bidirectional Review — 详细参考

## 报告输出模板

用户提交一批代码后，按此模板输出（替换占位内容）：

```markdown
# [页面/模块名] 双向评审报告

## 一、总评总结

**评审范围**：[列出本次涉及的文件/接口]
**整体评价**：[2–4 句概括优劣]
**问题统计**：高危 X 项 | 中危 X 项 | 低危 X 项

| 模块 | 主要优点 | 主要风险 |
|------|----------|----------|
| 前端 | … | … |
| 后端 | … | … |

---

## 二、【前端评审问题清单】

### [高危|中危|低危] 问题标题

**问题描述**：…
**不合理原因分析**：…
**优化整改方案**：…
**参考修改示例**：
\`\`\`tsx
// 关键片段
\`\`\`

（逐条重复）

---

## 三、【后端评审问题清单】

### [高危|中危|低危] 问题标题

**问题描述**：…
**不合理原因分析**：…
**优化整改方案**：…
**参考修改示例**：
\`\`\`python
# 关键片段
\`\`\`

（逐条重复）

---

## 四、整体优化优先级

### 紧急整改（立即处理）
1. …

### 中期优化（本迭代内）
1. …

### 长期重构建议
1. …

---

## 五、重构落地注意事项与改动风险提示

- …
```

---

## 前端评审检查清单

### 1. 布局结构合理性

- [ ] 页面信息层级清晰：主操作 / 次要信息 / 辅助说明是否分区明确
- [ ] 留白、间距、排版、卡片分区是否遵循项目 spacing scale（避免随意 `p-3`/`p-5` 混用）
- [ ] 是否存在内容拥挤、左右失衡、标题与正文对比不足
- [ ] 栅格布局（`grid`/`flex`）是否合理；`min-w-0` 等防溢出处理是否缺失
- [ ] 响应式：`sm`/`md`/`lg` 断点是否覆盖；小屏是否横向溢出、表格/图表是否可滚动
- [ ] 固定头/侧栏与内容区滚动是否冲突

### 2. UI 设计规范性

- [ ] 配色是否统一使用 `navy`/`gold`/`neutral` + 语义色；有无 `gray`/`slate`/`purple` 等杂色
- [ ] 圆角、阴影、字号是否对齐设计 tokens（如 `rounded-xl`、`shadow-card`）
- [ ] Icon 是否走 `ICON` 常量或统一 size；对齐、表意是否合理
- [ ] 按钮 variant 是否与场景匹配（primary / ghost / danger）
- [ ] **约束**：`components/ui/*` 内部实现问题不列入；仅评业务页是否误用 props、错误组合 class

### 3. 交互体验合理性

- [ ] 按钮/表单：loading、disabled、成功/错误反馈是否完整
- [ ] framer-motion：是否克制；有无与 CSS transition 冲突、无限动画、列表 stagger 过大
- [ ] 异常兜底：空数据、加载中、报错、网络异常是否有 `EmptyState`/Skeleton/Error 分支
- [ ] 表单：校验规则、防抖、防重复提交（提交中 disable + 请求锁）
- [ ]  destructive 操作是否有二次确认
- [ ] 路由跳转：离开未保存表单是否有提示（如适用）

### 4. 代码结构质量

- [ ] 组件拆分：单文件是否过大（>300 行需警惕）；职责是否混杂（数据获取 + 复杂 UI + 副作用）
- [ ] 重复逻辑是否应抽 Hook（分页、筛选、Modal 状态、表单）
- [ ] Tailwind：`cn()` 合并 vs 裸模板字符串；重复 6+ class 是否应抽组件或 `sf-*` 工具类
- [ ] 路由：懒加载、权限守卫、404 处理
- [ ] 接口：是否经 `services/`/`api` 层；组件内是否硬编码 URL
- [ ] `useEffect` 依赖是否完整；是否存在重复请求、缺少 cleanup、竞态未取消
- [ ] 渲染：不必要的内联对象/函数导致子组件重渲染

### 5. 专项问题

**ECharts**

- [ ] 是否使用 `charts/theme.js` / `build*ChartOption()` 而非页面散写配色
- [ ] 图例、tooltip、grid 边距是否合理；容器是否有明确高度
- [ ] `resize` / `ResizeObserver` 自适应；空数据时是否展示 EmptyState 而非空白 canvas

**Sonner**

- [ ] 成功/失败/警告类型是否与场景匹配
- [ ] 提示时机：是否在操作完成后；是否重复 toast 轰炸
- [ ] 文案是否用户可读（非原始 error.message 直出）

---

## 后端评审检查清单

### 1. 分层架构合理性

- [ ] App 按业务域拆分，职责单一
- [ ] View/ViewSet 仅编排：鉴权、调用 Service、返回响应
- [ ] Serializer 仅序列化与入参校验，无复杂业务分支
- [ ] 核心业务在 `services.py` 或领域服务层
- [ ] 是否存在 View 内大段 if/else、循环写库、跨 app 直接操作他域 Model

### 2. 数据库设计与 ORM 合理性

- [ ] 字段类型、长度、`null`/`blank`/`default` 是否合理
- [ ] 外键 `on_delete`、反向关系命名是否正确
- [ ] 高频查询字段是否有 `db_index` 或 `Meta.indexes`
- [ ] 列表接口是否 N+1：缺 `select_related` / `prefetch_related`
- [ ] 是否存在循环 `.save()`、应用层可合并的重复查询
- [ ] 冗余字段是否有同步策略；唯一约束是否靠 DB 层保障

### 3. 接口设计规范性

- [ ] RESTful：HTTP 方法、资源命名、嵌套路由语义
- [ ] 入参校验：Serializer / `validate_*` 是否覆盖非法值
- [ ] 统一响应体 `{ code, message, data }` 与错误码体系
- [ ] 分页：参数名、返回结构是否与前端拦截器一致
- [ ] 权限：`permission_classes`、对象级权限、越权（改他人 resource id）
- [ ] 异常：是否接入 DRF 全局异常处理，无裸 500 堆栈外泄

### 4. 业务逻辑严谨性

- [ ] 多表写是否 `transaction.atomic`
- [ ] 库存/名额/状态机是否有并发保护（`select_for_update` 或 DB 约束）
- [ ] 边界：空列表、已删除、重复提交、幂等
- [ ] 安全：用户输入 HTML 过滤、敏感字段 `write_only`、禁止 mass assignment
- [ ] 鉴权：操作是否校验资源归属

### 5. 工程可维护性

- [ ] 关键业务是否有 INFO 级操作日志（无敏感信息）
- [ ] 异常捕获是否具体类型，有上下文
- [ ] 废弃代码、未使用 import、重复 util 是否可清理
- [ ] 扩展性：硬编码 magic number、散落枚举字符串

---

## 示例问题条目

### 前端示例 — 中危：列表页缺少空态与加载态

**问题描述**：`OrderListPage` 在 `orders.length === 0` 时渲染空白区域，请求期间无 loading。
**不合理原因分析**：用户无法区分「加载中」与「无数据」，且不符合项目 `EmptyState` 使用规范。
**优化整改方案**：请求中展示 Skeleton；成功且为空时使用 `<EmptyState title="暂无订单" />`。
**参考修改示例**：

```tsx
if (isLoading) return <OrderListSkeleton />;
if (isError) return <ErrorState onRetry={refetch} />;
if (!orders.length) return <EmptyState title="暂无订单" description="去创建第一笔订单吧" />;
```

### 前端示例 — 低危：Tailwind 裸拼接与 token 偏离

**问题描述**：页面使用 `text-gray-400`、`rounded-lg` 与全站 `neutral-400`、`rounded-xl` 不一致。
**不合理原因分析**：破坏视觉统一，后续全站改版成本增加。
**优化整改方案**：替换为设计 tokens；重复 class 块改用 `Card` 或 `cn()` 组合。
**参考修改示例**：

```tsx
// Before
<div className="rounded-lg bg-gray-800 p-4 text-gray-400">

// After
<div className={cn('rounded-xl bg-navy-900 p-4 text-neutral-400')}>
```

### 后端示例 — 高危：更新订单状态缺少事务与行锁

**问题描述**：`OrderService.pay()` 先减库存再改订单状态，两步独立 commit。
**不合理原因分析**：并发下可能超卖或订单已支付库存仍被扣。
**优化整改方案**：`transaction.atomic()` + `select_for_update()` 锁商品行；失败整体回滚。
**参考修改示例**：

```python
from django.db import transaction

@transaction.atomic
def pay(order_id: int, user):
    order = Order.objects.select_for_update().get(pk=order_id, user=user)
    product = Product.objects.select_for_update().get(pk=order.product_id)
    if product.stock < order.quantity:
        raise BusinessError('库存不足')
    product.stock -= order.quantity
    product.save(update_fields=['stock'])
    order.status = Order.Status.PAID
    order.save(update_fields=['status'])
```

### 后端示例 — 中危：列表接口 N+1

**问题描述**：`OrderViewSet.get_queryset()` 未 prefetch `items`，Serializer 嵌套触发每单一次查询。
**不合理原因分析**：列表页数据量上升后响应时间线性恶化。
**优化整改方案**：`prefetch_related('items')` 或拆分列表/详情 Serializer。
**参考修改示例**：

```python
def get_queryset(self):
    return Order.objects.filter(user=self.request.user).prefetch_related('items')
```

---

## 优先级排序原则

| 优先级 | 判定标准 |
|--------|----------|
| 紧急整改 | 高危：安全、越权、数据一致性、核心功能不可用 |
| 中期优化 | 中危：性能隐患、关键体验缺失、明显架构违规 |
| 长期重构 | 低危 + 结构性债务：巨型文件拆分、枚举统一、文档补全 |

同一优先级内：**影响用户数 × 发生概率 × 修复成本** 综合排序。

---

## 重构落地注意事项

1. **分批改造**：单 PR 聚焦一个页面或一个 app，便于 review 与回滚
2. **公共组件边界**：业务页调整调用方式；不改 `components/ui` 内部（除非用户另开 UI 标准化任务）
3. **接口契约**：后端字段/路径变更须同步 [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md) 流程
4. **数据库变更**：必须 migration + 备份 + 回滚脚本，禁止手改表
5. **前端 v1.0 对齐**：评审中发现的接口不匹配，区分「前端适配」与「后端缺陷」，分别标注
6. **测试回归**：每批改动列出 smoke 清单（登录、列表、创建、编辑、删除、权限边界）
7. **Git**：建议 `review/fix-<module>-<topic>` 分支，小 commit

## 改动风险提示

| 改动类型 | 风险 | 缓解 |
|----------|------|------|
| 业务逻辑重构 | 行为变更 | 对照旧流程写用例；灰度 |
| 事务/锁 | 死锁、性能 | 压测；缩短锁持有时间 |
| 前端 Hook 抽取 | 隐性依赖遗漏 | 保持 props 签名；单页验证 |
| Serializer 字段变更 | 前端解析失败 | 兼容字段过渡期；版本文档 |
| 权限收紧 | 原可访问用户被拒 | 审计现有角色；公告 |

---

## 用户分批提交时的回复话术

材料到位：

> 已收到 [模块名] 批次，范围包括 …。以下为针对性双向评审报告。

材料不足：

> 基于已提供的 … 完成部分评审。建议下一批补充：`services/order.ts`、`OrderViewSet`、`OrderSerializer`、路由权限配置，以便评审接口链路与越权风险。

仅前端或仅后端：

> 本次仅收到前端代码，报告仅含【前端评审问题清单】；后端部分待补充接口与 Service 后继续。

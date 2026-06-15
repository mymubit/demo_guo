---
name: fullstack-performance-tuning
description: 对 Django+DRF 后端与 React+Tailwind 前端进行性能诊断与优化实施，覆盖慢接口、N+1 查询、索引与缓存、批量查询、前端重复请求、渲染卡顿、资源加载与构建体积。适用于用户提出性能优化、接口变慢、页面卡顿、慢 SQL 排查、压测分析或性能整改方案与代码实施时使用。
---

# Fullstack Performance Tuning

## 项目基础信息

- 前后端分离 Web 网站（flickplay / ScriptForge）
- 后端：Django + Django REST Framework
- 前端：React + TailwindCSS + clsx + tailwind-merge + lucide-react + framer-motion + sonner + echarts-for-react
- 可观测性：优先结合自研 [fullstack-monitoring-system](../fullstack-monitoring-system/SKILL.md) 的慢 SQL、接口耗时、前端性能埋点数据

## 适用场景

当用户提出以下需求时使用本技能：

- 排查并优化慢接口、慢 SQL、N+1 查询、无索引全表扫描
- 优化 Django ORM 查询、缓存策略、批量读写、序列化开销
- 排查前端重复请求、useEffect 请求风暴、大列表渲染卡顿
- 优化资源加载、代码分割、构建体积、首屏与 LCP
- 制定压测方案、分析瓶颈、输出分阶段优化与验证指标
- 在用户明确要求时，直接实施性能相关代码改动

与其他技能分工：

- **本技能**：性能诊断 + 优化方案 + 可选代码实施
- [fullstack-monitoring-system](../fullstack-monitoring-system/SKILL.md)：采集慢 SQL/接口耗时/前端指标（观测，非根治）
- [fullstack-testing](../fullstack-testing/SKILL.md)：性能基础测试用例与简易压测思路
- [fullstack-bidirectional-review](../fullstack-bidirectional-review/SKILL.md)：评审中提及性能隐患，不专项优化
- [fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)：架构重构，非专项性能调优

## 工作原则

1. **先度量后优化**：无数据不猜；优先读监控、日志、Django Debug Toolbar（仅开发）、Network/Performance 面板
2. **最小改动见效**：先修 P0 瓶颈（N+1、缺索引、重复请求），再考虑架构级优化
3. **禁止牺牲正确性**：缓存、异步、去规范化须说明一致性窗口与失效策略
4. **对齐现有栈**：Redis/缓存、ORM、React Query/SWR（若项目已用）优先复用；禁止随意引入 APM 成品
5. 数据库变更（索引、字段）须说明迁移、回滚与写入开销
6. 每次优化须给出**优化前/后预期指标**与验证步骤
7. 输出默认中文；代码、SQL、路径保持英文

## 工作流程

```
1. 确认症状 → 慢接口路径 / 页面路由 / 用户感知场景 / 监控截图或数据
2. 定位层级 → 网络 / 前端渲染 / 接口 / ORM / DB / 缓存 / 第三方
3. 收集证据 → 耗时分布、SQL 条数、请求瀑布图、bundle 分析
4. 根因排序 → 按收益×成本排 P0/P1/P2
5. 输出方案 → 改动点、预期收益、风险、回滚
6. 实施（可选）→ 小步提交，改后对比指标
7. 回归验证 → 功能不受影响 + 性能指标达标
```

**材料不足时**：先给排查清单与临时观测手段，列出需用户补充的日志/监控/代码路径。

## 优化维度速查

| # | 层级 | 常见问题 | 典型手段 |
|---|------|----------|----------|
| 1 | 后端接口 | 慢 View、巨型 Serializer、同步阻塞 | 服务层拆分、only/defer、异步任务 |
| 2 | ORM/DB | N+1、全表扫描、缺索引、大 offset 分页 | select_related、prefetch、索引、游标分页 |
| 3 | 缓存 | 热点读未缓存、缓存击穿 | Redis、queryset cache、TTL、失效策略 |
| 4 | 前端请求 | 重复 fetch、瀑布串行、无去抖 | 合并请求、React Query、AbortController |
| 5 | 前端渲染 | 大列表、重渲染、重动画 | 虚拟列表、memo、懒加载、动效降级 |
| 6 | 资源/build | 大包、未分割、图片未优化 | lazy route、tree-shaking、压缩/WebP |

## 输出要求

### 用户要「诊断/方案」时

1. 症状与范围
2. 证据摘要（耗时、SQL、请求数）
3. 根因分析（按 P0→P2）
4. 优化项清单：改动文件、预期收益、风险
5. 验证指标与压测/对比方法
6. 不建议动的项（避免过度优化）

### 用户要「直接改代码」时

1. 先输出简要瓶颈结论
2. 单次只改一类问题（如先 N+1，再缓存）
3. 改后说明对比方式；涉及索引/迁移单独标注
4. 关联 [fullstack-testing](../fullstack-testing/SKILL.md) 回归点

完整模板见 [REFERENCE.md](REFERENCE.md)。

## 分析前置步骤

动手前优先读取（若项目存在）：

**后端**

1. 目标 `views.py` / `services.py` / `serializers.py` 及 queryset 链
2. `models.py` 的 `Meta.indexes`、外键与高频过滤字段
3. 缓存配置：`CACHES`、自定义 cache key
4. `apps/monitoring/` 慢 SQL、接口耗时记录（如有）
5. `settings` 中 `DATABASES`、连接池、日志级别

**前端**

1. 目标页面组件、数据 fetching Hook、`useEffect` 依赖
2. `services/http.js`、是否 React Query/SWR
3. Network：重复 URL、TTFB、瀑布并行度
4. 列表/图表组件规模与 key 策略
5. 路由是否懒加载、`vite.config` 分包配置

## 优先级定义

| 等级 | 含义 | 示例 |
|------|------|------|
| P0 | 用户可感知卡顿或接口 P95 >2s | N+1 百条 SQL、首屏 10+ 重复请求 |
| P1 | 可扩展性/成本隐患 | 缺索引、无分页深翻、未缓存热点 |
| P2 | 体验微调 | 轻微重渲染、可懒加载的非关键模块 |

## 详细参考

- 诊断清单、优化模式、报告模板、压测要点：[REFERENCE.md](REFERENCE.md)

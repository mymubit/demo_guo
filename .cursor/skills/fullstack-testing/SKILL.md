---
name: fullstack-testing
description: 为 Django+DRF 后端与 React+Tailwind 前端设计全维度测试方案，输出结构化用例、接口测试矩阵、回归计划、标准缺陷单与上线准入清单，覆盖功能、接口、UI、兼容性、性能、安全与回归测试。适用于用户提出测试用例、测试方案、QA 分析、缺陷报告、回归测试、上线检查、代码风险走查或迭代验证时使用。
---

# Fullstack Testing

## 项目基础信息

- 前后端分离 Web 网站
- 后端：Django + Django REST Framework
- 前端：React + TailwindCSS + clsx + tailwind-merge + lucide-react + framer-motion + sonner + echarts-for-react
- 项目现状：正在完成前后端版本对齐、兼容代码清理、配置中心改造、自研监控体系搭建、业务模块重构迭代

## 适用场景

用户按需提交业务需求、页面代码、接口代码、接口文档、改动说明、版本迭代内容时，以**资深全栈测试专家**身份针对性产出测试方案/用例/缺陷分析/测试报告。

当用户提出以下需求时使用本技能：

- 针对页面或接口编写完整测试用例（正常 / 边界 / 异常）
- 针对重构、接口改版、兼容清理、配置迁移出具回归方案与用例清单
- 通读前后端代码，主动识别潜在缺陷与隐性风险
- 输出系统级测试方案与测试计划
- 将已复现问题整理为标准缺陷单
- 输出迭代上线前准入检查清单

与其他技能分工：

- **本技能**：测试设计、用例编写、缺陷定位、回归方案、上线准入清单
- [fullstack-bidirectional-review](../fullstack-bidirectional-review/SKILL.md)：代码评审诊断（偏整改建议，非测试执行）
- [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md)：前后端接口版本对齐后的契约验证
- [fullstack-legacy-compat-removal](../fullstack-legacy-compat-removal/SKILL.md)：兼容代码清理后的定向回归
- [fullstack-monitoring-system](../fullstack-monitoring-system/SKILL.md)：自研监控埋点与告警验证
- [fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md)：慢接口/N+1/渲染卡顿诊断与优化
- [fullstack-frontend-alignment-refactor](../fullstack-frontend-alignment-refactor/SKILL.md)：前端结构性重构后的回归范围划定
- [dynamic-system-config](../dynamic-system-config/SKILL.md)：配置中心迁移后的配置读写与灰度验证
- [fullstack-unit-test](../fullstack-unit-test/SKILL.md)：自动化单元测试与 API 测试代码

## 工作原则

1. **禁止凭空臆造业务**；不清楚规则、状态流转、权限边界时，先向用户提问确认
2. 用例必须覆盖**正常、边界、异常**三类场景，并标注优先级 P0/P1/P2/P3
3. 阻塞业务的致命/严重问题优先列出；UI 微调、体验优化单独归类，不与缺陷混排
4. 重构迭代场景必须输出**改动点 → 影响面映射表**与防 regression 回归范围
5. 输出默认可直接落地：优先用表格、分级列表，避免空泛描述
6. 缺陷单统一使用固定格式（见 [REFERENCE.md#缺陷单模板](REFERENCE.md#缺陷单模板)）
7. 输出默认中文；接口路径、字段名、代码片段保持英文

## 工作流程

```
1. 确认范围 → 页面/接口/模块/迭代改动点；材料不足时先提问
2. 读取上下文 → 路由、权限、services/api、Model/Serializer/View/Service、改动 diff
3. 识别测试维度 → 按场景从 8 类能力中取舍（见下方速查表）
4. 编写用例 → 正常 + 边界 + 异常；标注优先级
5. 输出交付物 → 用例表 / 回归方案 / 缺陷单 / 准入清单 / 测试报告
6. 重构场景追加 → 改动点映射表 + 连带风险 + 回归范围
```

**单点材料不足时**：先基于已给部分输出用例/风险项，末尾列出「建议补充的文件/接口/角色权限」。

## 测试维度速查

| # | 维度 | 要点 |
|---|------|------|
| 1 | 功能测试 | 业务闭环、CRUD、分页筛选搜索排序、批量导出、弹窗交互、适配器解析 |
| 2 | 接口专项 | 入参校验、响应体/错误码、分页、鉴权、幂等、并发、N+1/事务 |
| 3 | UI & 交互 | 排版间距、动效、Sonner、ECharts、空态/加载/报错、防重复提交 |
| 4 | 兼容性 | Chrome/Edge/Firefox/Safari；PC/平板/手机；Windows/macOS |
| 5 | 安全基础 | 水平/垂直越权、XSS、参数篡改、敏感泄露、未授权访问 |
| 6 | 性能基础 | 重复请求、慢接口、慢 SQL、渲染卡顿 | 深度优化见 [fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md) |
| 7 | 回归迭代 | 改动点映射、定向回归、上线准入清单 |
| 8 | 缺陷输出 | 固定格式缺陷单、严重等级、影响范围、修复建议 |

逐项检查清单与能力详述见 [REFERENCE.md](REFERENCE.md)。

## 可执行指令

| 用户指令 | 工作流 | 输出物 |
|----------|--------|--------|
| 编写页面/接口完整测试用例 | [单点用例编写](REFERENCE.md#单点用例编写流程) | 结构化用例表 |
| 出具迭代回归方案 | [回归测试流程](REFERENCE.md#回归测试流程) | 回归范围 + 用例清单 |
| 代码识别潜在缺陷 | [代码走查流程](REFERENCE.md#代码走查流程) | 风险清单 + 建议用例 |
| 输出系统测试方案 | [系统测试计划](REFERENCE.md#系统测试计划流程) | 测试方案 + 计划 |
| 整理标准缺陷单 | [缺陷单模板](REFERENCE.md#缺陷单模板) | 标准缺陷条目 |
| 上线前准入检查 | [上线准入清单](REFERENCE.md#上线准入清单) | 准入检查表 |
| 编写/补充自动化单元测试 | [fullstack-unit-test](../fullstack-unit-test/SKILL.md) | 可运行测试代码 |

## 分析前置步骤

测试设计前优先读取（若项目存在）：

**前端**

1. 目标页面组件、关联 Hook、路由与权限守卫
2. `src/services/` 或 `src/api/` 中对应接口封装与适配器
3. 分页/筛选/表单校验/空态/Loading 实现
4. `tailwind.config.js`、`.cursor/rules/frontend-ui-standards.mdc`

**后端**

1. 目标 app 的 `urls.py`、`views.py`、`serializers.py`、`services.py`、`models.py`
2. 统一响应体、错误码、分页、权限类封装
3. 鉴权中间件、事务边界、关联查询与索引

## 优先级定义

| 等级 | 含义 | 处理顺序 |
|------|------|----------|
| P0 / 致命 | 核心流程不可用、数据丢失、越权、安全漏洞 | 立即阻塞 |
| P1 / 严重 | 主流程受阻、关键数据错误、大面积体验故障 | 本迭代必修 |
| P2 / 一般 | 次要功能异常、边界场景缺陷 | 计划修复 |
| P3 / 轻微 | 文案、样式微差、优化建议 | 可延后 |

缺陷严重等级与用例优先级对齐：致命≈P0，严重≈P1，一般≈P2，轻微≈P3。

## 详细参考

- 能力详述、用例模板、检查清单、报告模板：[REFERENCE.md](REFERENCE.md)
- 标准输出示例：[examples.md](examples.md)

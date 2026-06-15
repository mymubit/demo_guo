---
name: fullstack-bidirectional-review
description: 对 Django+DRF 后端与 React+Tailwind 前端进行专业双向代码评审，分别输出前端页面/交互与后端业务逻辑评审报告，含风险等级、整改建议与代码示例。适用于用户提出页面评审、UI/UX 审计、后端逻辑评审、全栈代码审查、页面/API/模型架构评审或分批粘贴代码评审时使用。
---

# Fullstack Bidirectional Review

## 项目基础信息

- 前后端分离项目
- 后端：Django + Django REST Framework
- 前端：React + TailwindCSS + clsx + tailwind-merge + lucide-react + framer-motion + sonner + echarts-for-react
- 背景：前端停留在 v1.0，后端已多轮迭代，正在推进前端结构性重构对齐新版后端；**允许业务逻辑层面重构优化，全局基础公共组件固定不改动**

## 适用场景

用户分批粘贴页面、接口、模型、业务代码，要求**专业双向评审**时使用本技能：

- 前端页面设计 / 交互 / 代码结构评审
- 后端分层 / ORM / 接口 / 业务逻辑 / 可维护性评审
- 出具可落地整改建议，不推翻原有业务流程

与其他技能分工：

- **本技能**：评审诊断 + 整改建议，默认不直接改代码（除非用户明确要求实施）
- [fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)：架构重构落地方案
- [fullstack-ui-standardization](../fullstack-ui-standardization/SKILL.md)：全站 UI 规范化改版（纯样式）
- [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md)：前后端接口版本对齐
- [fullstack-frontend-alignment-refactor](../fullstack-frontend-alignment-refactor/SKILL.md)：前端结构性重构
- [fullstack-testing](../fullstack-testing/SKILL.md)：测试用例、回归方案、上线准入清单
- [fullstack-security-audit](../fullstack-security-audit/SKILL.md)：发布前安全审计
- [fullstack-release-deploy](../fullstack-release-deploy/SKILL.md)：生产部署与回滚
- [fullstack-performance-tuning](../fullstack-performance-tuning/SKILL.md)：性能瓶颈诊断与优化
- [fullstack-unit-test](../fullstack-unit-test/SKILL.md)：补充自动化单元/API 测试

## 硬性约束

1. **全局基础公共组件**（如 `components/ui/`）本身不做改动判定，仅评审业务页面如何调用、使用是否合理
2. 不推翻原有业务流程，只提优化整改方案
3. 评审必须基于用户**本次粘贴/指定的代码**，禁止凭猜测列问题
4. 前端 UI 规范对齐 `.cursor/rules/frontend-ui-standards.mdc`；后端对齐 `.cursor/rules/django-backend-standards.mdc` 与 `project-core-standards.mdc`
5. 输出默认中文；代码片段、路径、字段名保持英文

## 工作流程

用户分批提交材料时，按以下步骤执行：

```
1. 确认批次范围 → 页面/组件/Hook/路由/API/Model/Serializer/View/Service
2. 读取关联上下文 → 路由、请求封装、权限、公共组件引用、调用链
3. 逐维度检查 → 前端 5 类 + 后端 5 类（见 REFERENCE）
4. 仅对「有证据的问题」出清单 → 每条含：描述 / 原因 / 方案 / 示例
5. 汇总总评 → 风险等级 + 优先级排序 + 落地注意事项
6. 标注「需更多上下文才能判定」的项，不强行凑数
```

**单批次材料不足时**：先评审已给部分，末尾列出「建议下一批补充的文件/接口」。

## 输出格式（必须遵守）

完整模板见 [REFERENCE.md](REFERENCE.md#报告输出模板)。结构固定为：

1. **总评总结**：整体优劣、风险等级（低危 / 中危 / 高危阻塞）
2. **【前端评审问题清单】**：逐条四段式
3. **【后端评审问题清单】**：逐条四段式
4. **整体优化优先级**：紧急整改 > 中期优化 > 长期重构建议
5. **重构落地注意事项与改动风险提示**

每条问题格式：

```markdown
### [风险等级] 问题标题

**问题描述**：…
**不合理原因分析**：…
**优化整改方案**：…
**参考修改示例**：
\`\`\`tsx|python
// 关键片段
\`\`\`
```

## 评审维度速查

### 前端（5 类）

| # | 维度 | 要点 |
|---|------|------|
| 1 | 布局结构 | 信息层级、留白间距、栅格响应式 |
| 2 | UI 规范性 | 配色、圆角阴影字号、Icon 规范 |
| 3 | 交互体验 | 反馈、动效克制、异常兜底、表单校验防抖 |
| 4 | 代码结构 | 组件拆分、Hook 复用、Tailwind、路由权限、请求与 useEffect |
| 5 | 专项 | ECharts、Sonner |

### 后端（5 类）

| # | 维度 | 要点 |
|---|------|------|
| 1 | 分层架构 | App 拆分、View/Serializer/Service 职责 |
| 2 | 数据库 ORM | 字段关联、N+1、索引、约束 |
| 3 | 接口设计 | RESTful、校验、响应体、分页、权限越权 |
| 4 | 业务严谨性 | 事务、边界条件、并发、安全 |
| 5 | 可维护性 | 日志、异常、冗余代码、扩展性 |

逐项检查清单与示例见 [REFERENCE.md](REFERENCE.md)。

## 分析前置步骤

评审前优先读取（若项目存在）：

**前端**

1. `frontend/tailwind.config.js`、`src/styles/globals.css`
2. `frontend/src/components/ui/` — 公共组件 API（只读，不评审其内部实现缺陷）
3. `frontend/src/utils/cn.js`、`constants/iconSizes.js`、`constants/motion.js`
4. `frontend/src/components/charts/theme.js`
5. 目标页面的路由、权限守卫、services/api 调用

**后端**

1. 目标 app 的 `models.py`、`serializers.py`、`views.py`、`services.py`、`urls.py`
2. 项目统一响应/异常/分页/权限封装
3. 关联 Model 的外键与 `Meta.indexes`

## 风险等级定义

| 等级 | 含义 | 示例 |
|------|------|------|
| 高危阻塞 | 功能不可用、数据丢失、越权、安全漏洞 | 无事务超卖、IDOR、XSS 未过滤 |
| 中危 | 体验差、性能隐患、维护成本高 | N+1、缺 loading/空态、巨型页面 |
| 低危 | 规范不一致、可读性、小幅优化 | 间距不统一、重复 class、注释缺失 |

## 当用户要求「直接改代码」时

1. 先输出简要评审结论，再按**紧急 > 中期**顺序实施
2. 单次改动聚焦一类问题；不改全局公共组件内部实现
3. 涉及接口契约或 DB 变更须单独标注前后端影响
4. 改后说明关联测试点

## 详细参考

- 完整检查清单、报告模板、示例条目：[REFERENCE.md](REFERENCE.md)

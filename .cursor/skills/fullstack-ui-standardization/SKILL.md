---
name: fullstack-ui-standardization
description: 为 React+Tailwind 前端产出 Tailwind 设计规范、组件标准化方案与纯 UI 分阶段改版计划，不涉及业务逻辑与接口变更。适用于用户提出全站 UI 规范化、视觉一致性、设计 tokens、布局排版交互打磨、公共组件提取或 toast/chart/icon/动效标准时使用。
---

# Fullstack UI Standardization

## 项目基础信息

项目前端技术栈：React + TailwindCSS + clsx + tailwind-merge + lucide-react + framer-motion + sonner + echarts-for-react，后端 Django+DRF 前后端分离项目。

目前网站整体视觉观感杂乱、美观度不足，请帮我完成全站 UI 规范化改版方案。

## 硬性约束

- **只调整**布局、样式、排版、交互。
- **禁止修改**任何业务逻辑、接口请求、变量、数据结构。
- 不新增第三方 UI 库；优先复用 `frontend/src/components/ui`、`cn()`、`ICON`、`motion.js`、`charts/theme.js`。
- 与 `.cursor/rules/frontend-ui-standards.mdc` 保持一致；冲突时以本技能 + 现有 tokens 为准。

## 适用场景

- 输出 Tailwind 全局设计规范（色板、间距、圆角、阴影、字号阶梯）。
- 梳理 clsx/tailwind-merge、Lucide、framer-motion、sonner、ECharts 的统一用法。
- 规划公共基础组件封装与页面改版顺序。
- 执行**纯样式**批次改造（可独立自测、可回滚）。

## 分析前置步骤

动手改代码前必须先读取：

1. `frontend/tailwind.config.js` — 现有 tokens
2. `frontend/src/styles/globals.css` — CSS 变量与 `@layer components`
3. `frontend/src/components/ui/` — 已有公共组件
4. `frontend/src/utils/cn.js`、`constants/iconSizes.js`、`constants/motion.js`
5. `frontend/src/components/charts/theme.js`、`options.js`
6. `frontend/src/App.jsx` — Toaster 全局配置
7. 目标页面的 JSX class 与 inline 样式（抽样 2–3 个代表性页面）

## 输出要求

用户要「方案」时，按以下五段结构输出：

### 1. Tailwind 全局设计规范

基于现有 `navy` / `gold` / `neutral` 体系扩展，给出完整 tokens 表（见 [REFERENCE.md](REFERENCE.md#tailwind-全局设计规范)）：

- 主色、辅助色、中性色、语义色完整色值
- 间距 scale、圆角等级、阴影层级、字号阶梯
- 排版层级（标题 / 副标题 / 正文 / 辅助小字）

### 2. 常见问题整改思路

| 领域 | 项目现有入口 | 规范要点 |
|------|-------------|----------|
| class 合并 | `cn()` | 禁止裸模板字符串拼 class |
| 图标 | `ICON` 常量 | 尺寸 / 颜色 / 对齐 |
| 动画 | `constants/motion.js` | 禁止页面内自定义大幅动画 |
| Toast | `App.jsx` Toaster | 统一 classNames |
| 图表 | `charts/theme.js` + `options.js` | 禁止页面散写配色 |

详细模板见 [REFERENCE.md](REFERENCE.md#常见问题整改思路)。

### 3. 公共组件封装规划

优先**增强现有** `components/ui`，而非新建平行体系：

| 组件 | 文件 | 状态 |
|------|------|------|
| Button | `Button.jsx` | 已有，统一 variant |
| Card | `Card.jsx` | 已有 |
| Input/Select/Textarea | `FormControls.jsx` | 已有 |
| Modal | `Modal.jsx` | 已有 |
| Badge | `Badge.jsx` | 已有 |
| Pagination | `Pagination.jsx` | 已有 |
| EmptyState | `EmptyState.jsx` | 已有 |
| MetricCard | `MetricCard.jsx` | 数据卡片已有 |

缺失或需补充的封装清单见 [REFERENCE.md](REFERENCE.md#公共组件封装规划)。

### 4. 低风险分步改版执行顺序

```
Phase 0: 基线与样板页选定
Phase 1: 全局配置（tailwind + globals.css + Toaster）
Phase 2: 公共组件统一（ui/ 目录）
Phase 3: 样板页改版验证（1 用户页 + 1 管理页）
Phase 4: 全站批量微调（按路由分批）
Phase 5: 逐轮视觉回归自测
```

各 Phase 校验清单见 [REFERENCE.md](REFERENCE.md#分步改版执行顺序)。

### 5. 后续编码规范

Tailwind class 编写、组件拆分、样式复用、命名规范见 [REFERENCE.md](REFERENCE.md#后续编码规范)。

## 执行原则

1. **样式-only PR**：单个 PR 仅含 className / layout / CSS / 动画 / 图表 option 外观字段。
2. **先 tokens 后页面**：未统一 tokens 前不改业务页面。
3. **先组件后页面**：页面禁止复制 6+ 重复 Tailwind class，应改用 ui 组件或 `sf-*` 工具类。
4. **禁止混色**：不用 `gray/slate/purple/amber/red/green`，统一 `navy/gold/neutral` + 语义色。
5. **动画克制**：页面级仅 `pageEnter`；列表 `staggerChildren ≤ 0.06`；禁止无限 bounce/spin（loading 除外）。
6. **图表走工厂**：页面只传数据，样式走 `build*ChartOption()`。

## 当用户要求「直接改版」时

1. 确认目标页面/组件，列出将改的 **仅样式** 文件清单。
2. 单批次 ≤ 3 个文件或 1 个路由模块。
3. 改后立即：`npm run build` + 目视冒烟（布局、响应式、暗色、Toast、图表）。
4. 失败则 `git checkout --` 回滚该批次。

## 详细参考

- 完整色板、间距、组件 API、动画/Toast/图表模板：[REFERENCE.md](REFERENCE.md)
- 文件清理（非本技能）：[fullstack-cleanup-audit](../fullstack-cleanup-audit/SKILL.md)
- 架构重构（非本技能）：[fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)

# Fullstack UI Standardization — 详细参考

## Tailwind 全局设计规范

基于 `ScriptForge/frontend/tailwind.config.js` 与 `globals.css` 的 `:root` 变量，全站统一以下 tokens。**禁止**在页面中硬编码偏离色值。

### 色彩体系

#### 主色 — Navy（背景 / 表面 / 边框）

| Token | 色值 | 用途 |
|-------|------|------|
| `navy-950` | `#030d24` | 页面最深背景、scrollbar track |
| `navy-900` | `#051437` | 卡片背景、Toast 背景 |
| `navy-800` | `#0a1f44` | 抬升表面 `--sf-surface-raised` |
| `navy-700` | `#0f2a5c` | 边框基准 |
| `navy-600` | `#1a3a7a` | hover 边框 |
| `navy-500` | `#2d4f9e` | 次要强调 |
| `navy-400` | `#4d6db5` | 弱化文本、图标默认 |
| `navy-300` | `#8da7d3` | 副标题、description |
| `navy-200` | `#b3c5e1` | 正文浅色 |
| `navy-100` | `#d9e2f0` | 高亮正文 |
| `navy-50` | `#f0f4fa` | 极少用（深色主题下避免） |

CSS 变量映射：

```css
--sf-bg: navy-950
--sf-surface: navy-900
--sf-surface-raised: navy-800
--sf-border: rgba(141,167,211,0.18)
--sf-text: neutral-100 (#f1f5f9)
--sf-text-muted: neutral-400 (#94a3b8)
```

#### 辅助色 — Gold（CTA / 强调 / 焦点）

| Token | 色值 | 用途 |
|-------|------|------|
| `gold-500` | `#e0a008` | 主 CTA 渐变终点 |
| `gold-400` | `#f4b719` | 强调色、`--sf-gold`、focus ring |
| `gold-300` | `#f7cb54` | 标签、图表首色 |
| `gold-200` | `#fae08f` | hover 浅色 |

#### 中性色 — Neutral（文本层级）

| Token | 用途 |
|-------|------|
| `neutral-50`–`100` | 浅色文本（深色背景上） |
| `neutral-300`–`400` | 辅助小字、placeholder |
| `neutral-500`–`600` | 禁用、muted 图标 |
| `neutral-700`–`900` | 图表轴、分割线 |

#### 语义色（状态反馈）

| 语义 | 主色 | 背景/边框用法 |
|------|------|---------------|
| success | `success-500` `#22c55e` | `bg-success-500/12 border-success-500/35` |
| warning | `warning-500` `#f59e0b` | `bg-warning-500/12 border-warning-500/35` |
| danger | `danger-500` `#ef4444` | `bg-danger-500/12 border-danger-500/35` |
| info | `info-500` `#06b6d4` | `bg-info-500/12 border-info-500/35` |

#### 渐变色（仅用于 CTA / Hero / 品牌装饰）

| 名称 | 值 | 使用场景 |
|------|-----|----------|
| Primary | `#667eea → #764ba2` | 主按钮 `btn-primary` |
| Gold | `#f6d365 → #fda085` | 金色 CTA `btn-gold` |
| Navy | `#0a1f44 → #0f2a5c` | 面板 header |
| Body BG | `#030d24 → #051437 → #030d24` | body 背景 |

**禁止**：页面内新增 `#667eea` 以外的随机紫色渐变；统一走 `Button variant` 或 `globals.css` 工具类。

---

### 间距 Scale

基于 Tailwind 默认 4px 网格，业务系统推荐 subset：

| Token | 值 | 用途 |
|-------|-----|------|
| `1` | 4px | 图标与文字微间距 |
| `2` | 8px | 紧凑元素 gap |
| `3` | 12px | 表单字段内间距 |
| `4` | 16px | 卡片内 padding-sm、页面 px |
| `5` | 20px | — |
| `6` | 24px | 区块间距 `space-y-6` |
| `8` | 32px | 区块间距 lg `space-y-8` |
| `10` | 40px | 段落分隔 |
| `12` | 48px | section 上下边距 |

**页面壳层**（已有工具类）：

```html
<div class="sf-page-shell sf-section-stack">
  <!-- max-width 由 shell 控制，区块纵向 space-y-6 lg:space-y-8 -->
</div>
```

**禁止**：奇数 px（如 `p-[13px]`、`gap-[18px]`）除非对齐设计稿且写入 tokens。

---

### 圆角等级

| Token | 值 | 用途 |
|-------|-----|------|
| `rounded-lg` | 8px | 小标签、内嵌块 |
| `rounded-xl` | 12px | 按钮、输入框 |
| `rounded-2xl` | 16px | 卡片、面板、Toast、Modal |
| `rounded-card` | 1rem | tailwind extend，同 2xl |
| `rounded-panel` | 1.25rem | 大面板 |
| `rounded-full` | 9999px | Badge、Avatar |

---

### 阴影层级

| Token | 用途 |
|-------|------|
| `shadow-soft` | 轻微浮起（内嵌卡片） |
| `shadow-card` | 默认卡片 |
| `shadow-card-hover` | 可交互卡片 hover |
| `shadow-premium` | 主色 CTA |
| `shadow-gold` | 金色 CTA |
| `shadow-modal` | 弹窗 |

**规则**：同一视图最多 2 个阴影层级；禁止叠加 `shadow-lg shadow-xl shadow-2xl`。

---

### 字号阶梯与排版层级

| 层级 | Class | 字号/行高 | 字重 | 颜色 | 场景 |
|------|-------|-----------|------|------|------|
| Display | `text-4xl md:text-5xl` | 40–48 / tight | `font-bold tracking-tight` | `text-white` | 登录/Hero |
| H1 页面标题 | `text-2xl md:text-3xl` | 24–32 / 38–48 | `font-bold` | `text-white` | 页面顶栏 |
| H2 区块标题 | `text-xl` | 20 / 32 | `font-semibold` | `text-white` | Card header |
| H3 小节标题 | `text-lg` | 18 / 30 | `font-semibold` | `text-navy-100` | 表单分组 |
| 副标题 | `text-base` | 16 / 26 | `font-normal` | `text-navy-300` | 说明文字 |
| 正文 | `text-sm` | 14 / 22 | `font-normal` | `text-navy-200` | 列表、表格 |
| 辅助小字 | `text-xs` | 12 / 18 | `font-normal` | `text-navy-400` | 时间戳、hint |
| 标签/Badge | `text-xs` | 12 | `font-medium` | 语义色 | StatusBadge |

已有工具类：`section-title`、`section-subtitle`、`sf-label`、`sf-help-text`。

**行宽**：正文块 `max-w-2xl` 或 `max-w-3xl`；全宽表格不受限。

---

## 常见问题整改思路

### clsx / tailwind-merge 封装

项目已有 `cn()`（`utils/cn.js`），**所有**条件 class 必须经 `cn()`：

```jsx
import { cn } from '@/utils/cn'

// ✅
<div className={cn('sf-panel p-6', isActive && 'border-gold-400/40', className)} />

// ❌ 禁止
<div className={`sf-panel p-6 ${isActive ? 'border-gold-400/40' : ''}`} />
```

**重复 class 抽离规则**：

| 重复次数 | 动作 |
|----------|------|
| ≥ 6 个相同 utility | 抽为 `components/ui` 组件或 `globals.css` `@layer components` |
| 3–5 个 | 抽为局部常量 `const panelClass = '...'` 或复用 ui 组件 variant |
| 2 个 | 可 inline，优先 ui 组件 |

**variant 模式**（Button/Card 已示范）：

```jsx
const variants = {
  default: 'border border-navy-700/30 bg-navy-900/55',
  subtle: 'border border-navy-700/25 bg-navy-900/35',
}
className={cn(base, variants[variant], className)}
```

---

### lucide-react 图标规范

使用 `constants/iconSizes.js`：

| 场景 | ICON | 说明 |
|------|------|------|
| 按钮内图标 | `md` (16px) | 与 `text-sm` 按钮搭配 |
| 表格/列表操作 | `sm` (14px) | 紧凑行 |
| 页面标题装饰 | `lg`–`xl` | 20–24px |
| EmptyState | `empty` (48px) | 空状态居中 |
| Hero 装饰 | `hero` (56px) | 登录页等 |

**颜色**：

```jsx
<Icon className={cn(ICON.md, 'text-navy-400 group-hover:text-gold-400 shrink-0')} />
```

| 状态 | 颜色 class |
|------|------------|
| 默认 | `text-navy-400` |
| hover（在按钮/链接内） | 继承父级或 `group-hover:text-gold-400` |
| 激活/选中 | `text-gold-400` |
| 禁用 | `text-navy-600 opacity-50` |
| 危险操作 | `text-danger-400` |

**对齐**：图标+文字容器 `inline-flex items-center gap-2`；仅图标按钮用 `Button iconOnly` + `sr-only` 文案。

**禁止**：页面内 `w-5 h-5` 硬编码尺寸；禁止混用其他图标库。

---

### framer-motion 规范

统一使用 `constants/motion.js`，禁止页面内写 `transition={{ duration: 0.8, bounce: 0.5 }}`。

#### 允许的场景

| 场景 | 模板 | 说明 |
|------|------|------|
| 页面进入 | `pageEnter` | 路由级 wrapper |
| 卡片进入 | `cardEnter` | 列表首屏 |
| 列表 stagger | `listContainer` + `cardEnter` | stagger ≤ 0.06 |
| Modal | `modalOverlay` + `modalPanel` | 已有 Modal.jsx |
| 可交互卡片 | `hoverLift` | Card `interactive` |
| 按钮按压 | `pressTap` | 可选，`whileTap={pressTap}` |

#### 通用入场模板

```jsx
import { motion } from 'framer-motion'
import { pageEnter } from '@/constants/motion'

export function PageShell({ children }) {
  return (
    <motion.div {...pageEnter} className="sf-page-shell sf-section-stack">
      {children}
    </motion.div>
  )
}
```

#### Hover 模板

```jsx
<motion.div whileHover={hoverLift} className="sf-panel cursor-pointer">
```

#### 禁止

- `AnimatePresence` 嵌套超过 2 层
- `scale` 超过 1.05 或小于 0.92
- 无限循环动画（`node-active` 类仅用于进度指示）
- 页面背景 `particles-bg` 与 motion 叠加导致性能问题

---

### sonner Toast 全局配置

已在 `App.jsx` 配置，改版时**只改** `toastOptions.classNames` 和 `globals.css` 的 `.sf-toast`：

```jsx
<Toaster
  position="top-center"
  closeButton
  offset={20}
  toastOptions={{
    duration: 4200,
    classNames: {
      toast: 'sf-toast',
      title: 'text-sm font-semibold text-white',
      description: 'text-xs text-navy-300',
      actionButton: 'bg-gold-400 text-navy-950 hover:bg-gold-300',
      cancelButton: 'bg-navy-800 text-navy-200 hover:bg-navy-700',
      closeButton: 'border-navy-700 bg-navy-900 text-navy-300 hover:text-white',
      success: 'border-success-500/35',
      error: 'border-danger-500/35',
      warning: 'border-warning-500/35',
      info: 'border-info-500/35',
    },
  }}
/>
```

**调用规范**（不改业务文案，只统一样式入口）：

```jsx
import { toast } from 'sonner'
toast.success('操作成功')
toast.error('操作失败')
// 禁止 toast.custom 除非新增 variant 已写入 classNames
```

---

### ECharts 统一美化

**入口**：`components/charts/EChart.jsx` + `theme.js` + `options.js`。

#### 配色

- 系列色只用 `chartPalette`（首色 gold，其次 cyan/emerald/indigo…）
- 禁止页面 `itemStyle: { color: '#ff0000' }`

#### 边距 grid 标准

```js
grid: { left: 12, right: 16, top: 28, bottom: 12, containLabel: true }
// 有 legend 时 top: 46
```

#### 标题

```js
title: {
  text: '标题',
  subtext: '副标题',
  left: 0,
  textStyle: { color: '#f1f5f9', fontSize: 16, fontWeight: 600 },
  subtextStyle: { color: '#64748b', fontSize: 12 },
}
```

#### 图例

- 位置：`top: 0, right: 0` 或 `topLegend()` 工厂
- `itemWidth/Height: 10`，`textStyle.fontSize: 11`

#### 页面用法

```jsx
import EChart from '@/components/charts/EChart'
import { buildBarChartOption } from '@/components/charts/options'

<EChart option={buildBarChartOption({ labels, series })} height={280} />
```

**整改**：将页面内散写的 `option={{...}}` 迁移为 `build*ChartOption` 工厂函数（仅搬样式字段，不改 data 来源）。

---

## 公共组件封装规划

### 现有组件 API 标准

#### Button

```jsx
<Button variant="primary|gold|secondary|ghost|danger" size="sm|md|lg" isLoading iconLeft iconRight iconOnly />
```

#### Card

```jsx
<Card variant="default|glass|gold|subtle|flat" padding="none|sm|md|lg|xl" interactive />
```

#### FormControls

```jsx
<FieldShell label help error>
  <Input /> | <Select /> | <Textarea />
</FieldShell>
```

基类：`sf-control`、`sf-label`、`sf-help-text`。

#### Modal

- 使用 `modalOverlay` + `modalPanel` 动画
- 宽度：`max-w-md`（确认）/ `max-w-lg`（表单）/ `max-w-3xl`（复杂）

#### Badge / StatusBadge

- 圆角 `rounded-full`，`text-xs font-medium`
- 语义色边框 + 半透明背景

#### Pagination

- 统一 `Button variant="ghost" size="sm"` 作为页码按钮

#### EmptyState

- 图标 `ICON.empty`，标题 `text-lg font-semibold`，描述 `text-sm text-navy-400`

#### MetricCard

- 数字 `text-2xl font-bold text-white`，标签 `text-xs text-navy-400`

### 待补充/统一项

| 项 | 建议 |
|----|------|
| `PageHeader` | 标题 + 副标题 + actions 插槽，统一 H1 样式 |
| `SectionPanel` | 基于 `sf-panel` 的 titled section |
| `DataTable` 外观层 | 表头 `text-xs uppercase text-navy-400`，行 hover `bg-navy-800/30` |
| `Tabs` 外观 | 若多处重复，抽 ui/Tabs（仅样式） |
| `AdminUI` 对齐 | 管理后台与用户端共用 ui/ 组件 |

### 消除零散样式的迁移优先级

1. 裸 `<button className="btn-primary">` → `<Button variant="primary">`
2. 裸 `glass-card` div → `<Card variant="glass">`
3. 裸 input class → `<Input />`
4. 重复 empty 区块 → `<EmptyState />`

---

## 分步改版执行顺序

### Phase 0：基线与样板页选定

1. 分支：`git checkout -b ui/standardization-YYYYMMDD`
2. 记录基线 commit
3. 选定样板页：
   - 用户端：如 `pages/Works/index.jsx` 或 `pages/Creation/index.jsx`
   - 管理端：如 `pages/Admin/Dashboard.jsx`
4. 截图或录屏基线（可选）

**校验**：无代码变更。

---

### Phase 1：全局配置

**改动范围**：

- `tailwind.config.js` — 仅 extend tokens，不删现有色
- `globals.css` —  Consolidate 重复 `@apply`，补充缺失 `sf-*`
- `App.jsx` — Toaster classNames（如需）

**校验**：

```bash
cd frontend && npm run build
# 目视：任意页背景、字体、滚动条、Toast 样式正常
```

**回滚**：`git checkout -- tailwind.config.js src/styles/globals.css src/App.jsx`

---

### Phase 2：公共组件统一

**改动范围**：`components/ui/*.jsx` only

- 统一 variant 命名与 tokens 引用
- 移除组件内 hardcoded `indigo/purple`（Button primary 应对齐 navy/gold 体系或保留品牌渐变但统一一处）
- 确保全部使用 `cn()` + `ICON` + `motion.js`

**校验**：

```bash
npm run build
# Storybook 若有则跑；否则打开含 Button/Card/Modal 的页面冒烟
```

---

### Phase 3：样板页改版验证

**改动范围**：2 个样板页 + 其直接子组件（仅 className/layout）

**校验清单**：

- [ ] 响应式 sm/md/lg 无布局断裂
- [ ] 标题层级符合排版表
- [ ] 按钮/卡片/表单全部走 ui 组件
- [ ] 无新增 gray/slate 色
- [ ] 动画不突兀、无 layout shift
- [ ] 图表（若有）走 theme/options

**通过后**：将样板页模式固化为「页面模板」供 Phase 4 复制。

---

### Phase 4：全站批量微调

按路由模块分批，建议顺序：

1. `pages/Auth`、`pages/NotFound` — 低风险
2. `pages/Profile`、`pages/Member`、`pages/Wallet`
3. `pages/Works`、`pages/Creation`
4. `pages/Admin/**`
5. `components/creation/**`、`components/admin/**`

**每批规则**：

- ≤ 5 文件 / PR
- PR 标题：`ui: standardize {module} styles`
- 禁止同时改 `services/`、`store/`、hooks 逻辑

**校验**：`npm run build` + 该模块路由手动点击一遍。

---

### Phase 5：逐轮视觉回归自测

| 检查项 | 方法 |
|--------|------|
| 构建 | `npm run build` |
| 色板一致性 | `rg "gray-|slate-|purple-|amber-" frontend/src/pages` 趋近零 |
| 图标尺寸 | `rg "w-[0-9] h-[0-9]" frontend/src/pages` 审查 Lucide |
| 动画 | 目视无多余 AnimatePresence |
| Toast | 触发 success/error 各一次 |
| 图表 | Admin Dashboard 图表可读 |
| 业务回归 | 登录、核心 CRUD、Creation 流程 |

**回滚**：按 PR revert，不跨批 cherry-pick。

---

## 后续编码规范

### Tailwind class 编写

1. **顺序**：布局 → 尺寸 → 间距 → 边框 → 背景 → 文字 → 效果 → 状态 → 响应式
2. **条件**：必须 `cn()`
3. **长度**：单行 class 超过 ~120 字符则抽组件
4. **颜色**：只用 tokens 表内色系
5. **响应式**：移动优先，`sm:` `md:` `lg:` 最多 3 断点

### 组件拆分

| 类型 | 位置 |
|------|------|
| 纯 UI、无业务 | `components/ui/` |
| 领域 UI、无请求 | `components/{domain}/` |
| 含 API 的容器 | 保持原位，仅外层套 ui 组件 |

**禁止**：为改版新建平行 `Button2.jsx`。

### 样式复用优先级

1. `components/ui` 组件 props
2. `globals.css` 的 `sf-*` / `btn-*`
3. tailwind.config `extend`
4. 页面 local 常量
5. 内联 arbitrary values（最后手段）

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| UI 组件文件 | PascalCase | `MetricCard.jsx` |
| variant 键 | camelCase 语义 | `primary`, `subtle` |
| CSS 工具类 | `sf-` 前缀 | `sf-panel`, `sf-control` |
| motion 导出 | camelCase 名词 | `pageEnter`, `hoverLift` |
| 图表工厂 | `build` + 类型 + `ChartOption` | `buildBarChartOption` |

### PR 审查要点（样式-only）

- [ ] 无 `services/`、`store/`、API 路径变更
- [ ] 无 props 语义变更、无数据结构变更
- [ ] diff 主要是 className、layout、CSS
- [ ] 使用 ui 组件或 sf-* 而非复制粘贴
- [ ] build 通过

---

## 输出示例：页面标题区块模板

```jsx
import { Button, Card } from '@/components/ui'
import { Plus } from 'lucide-react'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'

function PageHeader({ title, subtitle, actionLabel, onAction, className }) {
  return (
    <div className={cn('flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between', className)}>
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">{title}</h1>
        {subtitle ? <p className="text-sm text-navy-300 md:text-base">{subtitle}</p> : null}
      </div>
      {actionLabel ? (
        <Button variant="gold" iconLeft={<Plus className={ICON.md} />} onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}
```

此模板仅示范排版与组件用法，**不引入新业务逻辑**。

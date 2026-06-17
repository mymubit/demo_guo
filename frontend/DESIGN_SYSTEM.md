# ScriptForge · UI/UX 设计体系（标准化参考文档）

> ✅ 设计令牌（Tokens） ✅ 组件库（Components） ✅ 页面范式（Pages） ✅ 交互规范（Interaction）

## 1. 设计令牌 · Design Tokens

所有颜色、字号、间距、圆角、阴影、动效全部在此定义，并与 `tailwind.config.js` 1:1 对齐。

### 1.1 色彩体系

| Token Name | Value | Usage |
|-----------|-------|-------|
| `brand-500` | `#6366f1` | 主品牌色 — 主要 CTA、重点强调 |
| `brand-600` | `#4f46e5` | 主品牌 hover / active |
| `accent-400` | `#f4b719` | 金色强调 — 高分、亮点 |
| `accent-300` | `#f7cb54` | 金色 hover |
| `slate-50 ~ slate-950` | `#f1f5f9 ~ #030d24` | 中性层级 — 文本/背景/边框 |
| `success` | `#22c55e` | 成功 / 已上线 / 通过 |
| `warning` | `#f59e0b` | 警告 / 待审核 / 运行中 |
| `danger` | `#ef4444` | 错误 / 删除 / 失败 |
| `info` | `#06b6d4` | 信息提示 |

**Tailwind 使用方式（规范）**

```tsx
// ✅ 正确: 使用语义化类
className="bg-brand-500 text-white hover:bg-brand-600"
className="border-success-border text-success-light"

// ❌ 避免: 硬编码色值
className="bg-indigo-500"   // → 应改为 bg-brand-500
className="text-yellow-400" // → 应改为 text-accent-300
```

### 1.2 字号与行高

| Token | 字号 | 行高 | 适用场景 |
|-------|------|------|---------|
| `text-xs` | 12px | 18px | 辅助标签、徽章 |
| `text-sm` | 13px | 20px | 正文小字 |
| `text-base` | 14px | 22px | 默认正文 |
| `text-md` | 15px | 24px | 较大正文 |
| `text-lg` | 16px | 26px | 小标题 |
| `text-xl` | 18px | 28px | 区块标题 |
| `text-2xl` | 20px | 30px | 页面标题 |
| `text-3xl` | 24px | 32px | KPI 数字 |

### 1.3 间距 · Spacing

统一以 `4px` 为基准（8-point 栅格）:

| Token | 像素 | 适用场景 |
|-------|------|---------|
| `p-1` | 4px | 图标内边距 |
| `p-2` | 8px | 小组件内边距 |
| `p-3` | 12px | 卡片内边距 |
| `p-4` | 16px | 面板内边距 |
| `p-5` | 20px | 大卡片 |
| `p-6` | 24px | 区块 |
| `gap-3` | 12px | 组件间距 |
| `gap-4` | 16px | 列表项间距 |

### 1.4 圆角与阴影

| Token | 值 | 适用场景 |
|-------|---|---------|
| `rounded-lg` | 14px | 中等卡片 |
| `rounded-card` | 18px | 标准卡片 |
| `rounded-panel` | 20px | 大面板 |
| `rounded-full` | 9999px | 徽章/按钮 |
| `shadow-[panel/card/modal]` | 自定义 | 各层级阴影 |

### 1.5 动效

**统一时长**: `150ms / 250ms / 350ms`
**统一缓动**: `cubic-bezier(0.4, 0, 0.2, 1)`

| 动效 | 时机 |
|------|------|
| `animate-fade-in` | 入场淡入 |
| `animate-pulse-glow` | 执行节点/活跃状态 |
| `transition-all duration-200` | 悬停、状态变化 |

## 2. 组件规范

### 2.1 Button 按钮

**变体**（6 种）：`brand` / `accent` / `secondary` / `ghost` / `danger` / `text`
**尺寸**（4 种）: `xs` / `sm` / `md` / `lg`

```tsx
import Button from '@/components/ui/Button.jsx'
import { Plus } from 'lucide-react'

// ✅ 主操作按钮
<Button variant="brand" iconLeft={<Plus className="w-4 h-4" />}>新建技能</Button>

// ✅ 次要操作
<Button variant="secondary">取消</Button>

// ✅ 危险操作
<Button variant="danger" onClick={handleDelete}>删除</Button>

// ✅ 图标按钮
<Button variant="ghost" size="sm" iconOnly icon={<Eye className="w-3.5 h-3.5" />} aria-label="查看" />
```

**一个操作区域内按钮数量**:

- 最多 **1 个主按钮** (`brand` / `accent`)
- 其他全部使用 `secondary` / `ghost`

### 2.2 Badge 徽章

**Tones**（7 种）: `brand` / `accent` / `success` / `warning` / `danger` / `info` / `default`

```tsx
import { Badge } from '@/components/ui/Badge.jsx'

<Badge tone="success" size="sm">已上线</Badge>
<Badge tone="warning">待审核</Badge>
<Badge tone="danger">已下线</Badge>
<Badge tone="brand">v1.2.3</Badge>
```

### 2.3 EmptyState 空状态

```tsx
import EmptyState from '@/components/ui/EmptyState.jsx'

// 基础空状态
<EmptyState type="no-data" title="暂无技能" description="点击下方按钮创建第一个技能" />

// 带操作按钮
<EmptyState
  type="empty-create"
  title="还没有项目"
  description="创建项目后即可开始短剧创作"
  action={<Button variant="brand" size="sm">新建项目</Button>}
/>

// 网络异常
<EmptyState type="network-error" />
```

### 2.4 AdminShell 管理页面壳

所有 `/admin/*` 页面必须使用 `AdminShell` 作为最外层。

```tsx
import AdminShell, { AdminToolbar, AdminTable, AdminPagination } from '@/components/admin/AdminShell.jsx'

<AdminShell
  title="技能管理"
  description="管理短剧创作平台的全部技能"
  breadcrumbs={[{ label: '创作中心', href: '/admin/creation' }]}
  actions={<Button variant="brand">新建技能</Button>}
  toolbar={
    <AdminToolbar>
      {/* 搜索 / 筛选 */}
    </AdminToolbar>
  }
>
  {/* 表格内容 */}
</AdminShell>
```

## 3. 页面范式

### 3.1 管理列表页（标准范式）

```
┌──────────────────────────────────────────┐
│ 面包屑（可选）                            │
│  标题 · 描述                    [新建]   │  ← AdminShell.header
├──────────────────────────────────────────┤
│ [搜索] [筛选1] [筛选2]    [批量操作 ▼]  │  ← AdminToolbar
├──────────────────────────────────────────┤
│ KPI 卡片网格 (可选)                      │  ← AdminKpiCard × n
├──────────────────────────────────────────┤
│ 列1 | 列2 | 列3 | 状态 | 操作           │  ← AdminTable
│ ─────────────────────────               │
│ 数据 | 数据 | 数据 | ●    | 编辑 删除   │
├──────────────────────────────────────────┤
│                [分页]                     │  ← AdminPagination
└──────────────────────────────────────────┘
```

### 3.2 表单页规范

- 字段分组: 使用 `AdminPanel` 包裹每组字段
- 必填标记: 只在必填字段的 label 前加 `*`
- 提交按钮: 固定在底部或右下角, 主操作 (`brand`) 在最右
- 取消按钮: `secondary` 或 `text` 变体
- 错误提示: 字段内联红边 + 红文描述

## 4. 交互反馈规范

### 4.1 Toast 消息

统一使用 `useToast()` hook。

```tsx
const { success, error, warning, info } = useToast()

// ✅ 操作成功
success('创建成功', '已新增技能 · 剧本大纲生成器')

// ✅ 操作失败
error('创建失败', '配额不足,请联系管理员')

// 统一文案规则: 简洁动词 + 结果
```

### 4.2 加载状态

- 页面整体加载: 使用 `SkeletonPage`
- 列表加载: 使用 `AdminTable(isLoading=true)`
- 按钮加载: `<Button isLoading>`

### 4.3 禁用态

- 禁用按钮: 使用 `disabled` 属性, 统一 `opacity-60 cursor-not-allowed`
- 禁用输入: 自动套用 Tailwind `disabled:` 修饰

## 5. 响应式规范

| 断点 | 典型场景 | 布局策略 |
|------|---------|---------|
| `sm` (640px+) | 小屏手机 | 单列, 隐藏次要操作列 |
| `md` (768px+) | 平板/小笔记本 | 2-3 列, 工具栏折行 |
| `lg` (1024px+) | 桌面 | 3-4 列, 完整工具栏 |
| `xl` (1280px+) | 大屏 | 完整布局 |

```tsx
// ✅ 响应式网格
className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"

// ✅ 响应式表格隐藏列
{ key: 'quota', title: '配额', className: 'hidden lg:table-cell' }
```

## 6. 新增组件/页面的标准流程

1. **查库** — 在 `components/ui/`、`components/admin/` 中查找是否已有相似组件
2. **确定变体/尺寸** — 不新增加 `variant` / `tone`, 优先复用现有
3. **参考此文档** — 检查交互反馈/空状态/加载等是否规范
4. **在 `components/index.js` 导出** — 统一入口
5. **在页面中引用** — `import X from '@/components/...'`

## 7. 错误修正与重构规则

**不要做的事情** ❌

- 不要在页面组件内直接写 `bg-indigo-500` — 使用 `bg-brand-500`
- 不要新增 `text-[13px]` 等硬编码字号 — 统一使用 `text-sm / text-base`
- 不要新增自定义 keyframes — 先查 `constants/motion.js`, 有就复用,没有再添加
- 不要绕过 `useToast()` 直接写 toast 消息

**应该做的事情** ✅

- 遇到散落的样式, 封装为语义化组件
- 遇到散落的逻辑, 封装为可复用的 hook
- 发现设计缺陷, 更新此文档 → 更新 tailwind.config.js → 全局搜索替换

## 8. 文件索引

| 路径 | 内容 |
|------|------|
| `tailwind.config.js` | 设计令牌主配置（色彩/字号/阴影/圆角/动效） |
| `src/styles/globals.css` | 全局基础样式 + 业务专用 CSS 类 |
| `src/components/ui/` | 基础组件（Button / Badge / EmptyState / Skeleton） |
| `src/components/admin/` | 管理后台组件（AdminShell / AdminTable 等） |
| `src/constants/motion.js` | 动画 / 动效规范 |
| `src/hooks/useToast.js` | 统一消息反馈 |
| `src/pages/Admin/AdminSkills.jsx` | 标准管理页面参考实现 |


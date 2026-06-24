# 深色电影主题更新计划

## 概览
将 BrandLogo 和 AdminLayout 更新为 navy 底色 + 金色品牌色的深色电影主题，保持所有 props 和功能兼容。

---

## 1. BrandLogo.jsx 修改

**文件**: `/workspace/frontend/src/components/ui/BrandLogo.jsx`

### 修改点：

#### (1) SIZE_MAP 统一 film 图标颜色
- 所有尺寸的 film 图标统一为 `text-navy-950`（金色背景上的深色）
- sm 尺寸的 box 显式添加 `rounded-xl` 保持一致
- 变更：
  - sm: `{ box: 'w-10 h-10 rounded-xl', icon: ICON.lg, film: 'text-navy-950' }`
  - md: film 保持 `text-navy-950`（不变）
  - lg: film 从 `text-white` 改为 `text-navy-950`

#### (2) 文字颜色按 variant 区分
- **consumer 变体**（默认/C端）：
  - 品牌名 ScriptForge：`text-gold-400 group-hover:text-gold-300`（金色系+hover变亮）
  - 副标题/AI：`text-slate-400`
- **admin 变体**（深色背景侧边栏用）：
  - 品牌名 ScriptForge：`text-white group-hover:text-gold-300`（白色hover变金）
  - 副标题：`text-slate-400`
- 外层包裹 span 从 `text-gray-900` 改为适配深色主题的样式
- 移除旧的 `text-gray-900`、`text-brand-600`、`text-gray-500` 等浅色类

#### (3) 保持所有现有逻辑
- 保留全部 props：size/variant/showText/subtitle/to/interactive/className
- 保留 motion 动画、Link 包裹、条件渲染等逻辑不变

---

## 2. AdminLayout.jsx 修改

**文件**: `/workspace/frontend/src/components/layout/AdminLayout.jsx`

### 修改点：

#### (1) 侧边栏背景
- 从 `bg-gradient-to-b from-navy-900 via-navy-950 to-navy-950 border-r border-white/5`
- 改为 `bg-navy-900 border-r border-white/10`

#### (2) 侧边栏 Logo 区域
- 使用 `BrandLogo variant="admin" size="lg" showText subtitle="运营控制台"` 替代当前的 showText={false} + 自定义文字 div
- 移除自定义的 "ScriptForge" gradient-text div 和 "运营控制台" div（由 BrandLogo 内部渲染）
- BrandLogo admin 变体内部已使用白色文字适配深色背景
- 保留用户信息卡片（头像、管理员名、运营账号），文字颜色适配 slate 色系

#### (3) 侧边栏导航链接（NavItem 组件）
- **默认状态**：`text-slate-400 hover:text-white hover:bg-white/10`（原 text-navy-200 hover:bg-white/[0.06]）
- **active 状态**：`bg-gold-500/15 text-gold-300 border-l-2 border-gold-400`（原 bg-gold-500/16 text-gold-50 + 左侧渐变圆条）
- 移除 active 状态的 `shadow-sm shadow-gold-500/10`
- 移除左侧绝对定位的 w-1 rounded-full 渐变条（改用 border-l-2）
- 图标颜色同步：active 时 `text-gold-400`，默认 `text-slate-400 group-hover:text-white`
- 移除 font-semibold/font-medium 不一致问题，统一 font-medium

#### (4) 侧边栏分组标题
- 从 `text-[15px] font-semibold` 改为 `text-slate-500 text-xs uppercase tracking-wider`
- 可折叠组按钮的 hover/active 颜色适配：默认 text-slate-500，hover:text-slate-300，active group 时 text-gold-400
- ChevronDown 图标颜色同步调整

#### (5) 顶部栏
- 背景从 `bg-navy-950/95` 改为 `bg-navy-950/80`
- 面包屑非当前项：从 `text-navy-400` 改为 `text-slate-400`
- 面包屑分隔符 ChevronRight：从 `text-navy-500` 改为 `text-slate-500`
- 顶部右侧退出按钮：从 `text-navy-400 hover:bg-white/[0.06]` 改为 `text-slate-400 hover:text-red-300 hover:bg-red-500/10`

#### (6) 主内容区
- 背景从 `bg-gradient-to-b from-[#0a0e1a] to-[#0e1424]` 改为 `bg-navy-950 text-slate-200`

#### (7) 页脚
- 侧边栏底部（退出按钮区域）：border 保持 `border-t border-white/5`（从 border-white/10 调整）
- 页面底部页脚：从 `text-navy-400` 改为 `text-slate-500`

#### (8) 退出按钮（侧边栏）
- 从 `text-navy-400 hover:text-red-400 hover:bg-red-500/5`
- 改为 `text-red-400 hover:bg-red-500/10 hover:text-red-300`

#### (9) 移动端菜单按钮
- 添加 `border border-white/10 bg-white/5`
- 文字从 `text-navy-300` 改为 `text-slate-200`
- hover 状态适配深色主题

#### (10) 全局浅色类清理
- 用户卡片中 `text-navy-400` → `text-slate-400`
- 确保无 `bg-gray-100`、`bg-white`（非透明）、`text-gray-xxx` 等浅色类残留

---

## 注意事项
- 所有 props 保持向后兼容
- 不修改 constants/brand.js（渐变/阴影保持不变）
- 不修改其他任何文件
- 所有交互逻辑（折叠状态、导航、退出登录、面包屑等）完全保留

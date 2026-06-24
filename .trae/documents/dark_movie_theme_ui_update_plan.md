# 深色电影主题 UI 组件更新计划

## 概述
将3个UI组件（Button、Card、Badge）和App.jsx中的toast样式更新为深色电影主题（navy底色+金色品牌色），保持所有props和导出兼容。

## 修改文件清单

### 1. /workspace/frontend/src/components/ui/Button.jsx
**修改内容：**
- 更新 `variants` 对象：
  - `brand`/`primary`/`gold`/`accent`：改为金色渐变背景 `bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950 shadow-gold hover:from-gold-200 hover:to-gold-400 hover:-translate-y-0.5 hover:shadow-gold-lg`
  - `secondary`：改为 `border border-white/10 bg-white/5 text-slate-200 hover:border-white/20 hover:bg-white/10`
  - `ghost`：改为 `border border-transparent text-slate-300 hover:bg-white/5 hover:text-white`
  - `danger`：改为 `border border-danger/30 bg-danger/10 text-danger-light hover:bg-danger/20`
  - `text`：改为 `text-gold-400 hover:text-gold-300`
- 更新 `focus-visible` ring：改为 `ring-gold-500/30 ring-offset-navy-950`
- 保持 sizes、iconOnly、isLoading 等所有现有逻辑不变

### 2. /workspace/frontend/src/components/ui/Card.jsx
**修改内容：**
- 更新 `variants` 对象为深色风格：
  - `default`：`border border-white/8 bg-white/[0.04] backdrop-blur-sm rounded-card shadow-card`
  - `glass`：`border border-white/10 bg-white/[0.06] backdrop-blur-md`
  - `elevated`：`border border-white/10 bg-slate-900/60 shadow-lg`（新增变体）
  - `subtle`：`border border-white/5 bg-white/[0.02]`
  - `gold`：`border border-gold-500/20 bg-gold-500/10`
  - `flat`：`border border-white/8 bg-white/[0.03]`
- 更新 interactive 时 hover 效果：`hover:border-gold-500/30 hover:bg-white/[0.08] hover:-translate-y-0.5 hover:shadow-card-hover transition-all`
- 保持 paddings、as、motion 等所有现有逻辑不变

### 3. /workspace/frontend/src/components/ui/Badge.jsx
**修改内容：**
- 更新所有 `tones` 为深色背景（带透明度）+ 对应主题色文字/边框：
  - `brand`/`gold`/`accent`：`bg-gold-500/15 border-gold-500/30 text-gold-300`
  - `success`：`bg-success/12 border-success/30 text-success-light`
  - `warning`：`bg-warning/12 border-warning/30 text-warning-light`
  - `danger`：`bg-danger/12 border-danger/30 text-danger-light`
  - `info`：`bg-info/12 border-info/30 text-info-light`
  - `default`：`bg-white/8 border-white/10 text-slate-300`
- 保持 sizes、StatusBadge、导出等所有现有逻辑不变

### 4. /workspace/frontend/src/App.jsx
**修改内容：**
- 更新 toast classNames：
  - `cancelButton`：改为 `'bg-navy-800 text-slate-300 hover:bg-navy-700'`
  - `actionButton`：保持 `'bg-gold-400 text-navy-950 hover:bg-gold-300'`（已正确，确认即可）

## 兼容性保证
- 所有组件的 props 接口保持不变
- 所有导出保持不变
- 不修改其他任何文件

# Home 页面深色电影主题重写计划

## 文件修改
- 修改文件：`/workspace/frontend/src/pages/Home/index.jsx`（完整重写）

## 现有问题分析
1. **Bug**：第454行使用`useStateOpen`（错误别名），第487行末尾有错误的`import { useState as useStateOpen } from 'react'`
2. **浅色主题**：页面整体使用`bg-gray-50`/`white`/`gray-200`等浅色背景，不符合深色电影主题
3. **36角色文案**：TESTIMONIALS中林**的评价提到"Drama Skills 36角色体系"
4. **路由问题**：两处`/creation`需要改为`/drama`
5. **彩色图标**：FEATURES中使用多种彩色（#667eea, #f6ad55, #68d391等）

## UI组件系统确认
- **Card**组件支持`variant="glass"`：`border border-white/10 bg-white/[0.06] backdrop-blur-md`
- **Card**组件支持`variant="gold"`：`border border-gold-500/20 bg-gold-500/10`
- **Button**组件：
  - `variant="brand"`/`"gold"`：金色渐变背景 + navy文字（CTA按钮）
  - `variant="secondary"`：边框白色半透明 + slate文字
  - `variant="ghost"`：透明背景 + slate文字
- **Badge**组件：
  - `tone="gold"`：金色半透明背景
  - `tone="info"`：info深色版本

## 重写要点

### 1. 导入修复
- 在文件顶部正确添加`import { useState } from 'react'`
- 删除文件末尾的错误导入`import { useState as useStateOpen } from 'react'`
- 从`@/components/ui`导入`Card`组件
- FAQItem中使用正确的`useState`

### 2. 全局背景
- 最外层div：`bg-navy-950`替代`bg-gray-50`
- 所有section使用深色背景，不再使用浅色

### 3. Hero区域
- **背景**：`bg-navy-950`，添加radial-glow径向光效果，使用HERO_BG作为暗色遮罩背景
- **边框**：移除`border-b border-gray-200`，改为`border-b border-white/5`
- **Badge**：保持`tone="gold"`和`tone="info"`（已是深色版本）
- **标题**：`text-white`，高亮部分使用金色渐变`from-gold-300 to-gold-500`
- **描述**：`text-slate-300`替代`text-gray-600`
- **按钮**：
  - 主按钮：`variant="brand"`（金色渐变，navy文字），路由改为`/drama`
  - 次按钮：`variant="ghost"`
- **统计卡片**：使用`Card variant="glass"`替代`sf-surface-card`，数值白色/金色，标签slate-400
- **海报卡片**：深色玻璃态效果，边框`border-white/10`，标签使用深色背景

### 4. 功能区域
- **背景**：保持`bg-navy-950`
- **标题**：`text-white`，`ScriptForge`使用金色渐变
- **描述**：`text-slate-400`
- **功能卡片**：使用`Card variant="glass" interactive`
- **图标**：统一使用金色系（gold-400/gold-500），背景使用`bg-gold-500/10`，移除所有彩色color字段
- **卡片标题**：`text-white`，描述`text-slate-400`

### 5. 题材区域
- **背景**：深色
- **标题**：白色，金色高亮
- **描述**：text-slate-400
- **题材卡片**：使用`Card variant="glass" interactive`，移除`sf-surface-card`
- **标签文字**：text-slate-400

### 6. Drama Skills流程区域
- **标题**：白色
- **描述**：text-slate-300
- **流程卡片**：使用`Card variant="glass"`
- **连接线**：金色渐变（from-transparent via-gold-500/50 to-transparent）
- **流程节点三种状态**：
  - `active`：`bg-gold-500 text-navy-950 shadow-gold`（金色填充深色文字）
  - `done`：`border-gold-500/30 bg-gold-500/10 text-gold-300`（金色边框半透明背景）
  - `idle`：`border-white/10 bg-white/5 text-slate-500`（深色边框灰色文字）
- **进度条**：背景`bg-white/10`，填充`bg-gradient-to-r from-gold-400 to-gold-500`
- **状态文字**：当前状态白色/金色，其他slate-400

### 7. 用户评价
- **标题**：白色，金色高亮数字
- **评价卡片**：使用`Card variant="glass"`
- **星级**：金色（text-gold-400 fill-gold-400）
- **评价内容**：text-slate-300
- **头像**：金色渐变（from-gold-400 to-gold-600），文字navy-950
- **用户名**：text-white，角色text-slate-400
- **文案替换**：林**评价中的"Drama Skills 36角色体系"改为"Drama Skills 12位专业角色体系"

### 8. FAQ区域
- **标题**：白色，描述text-slate-400
- **FAQ卡片**：`border-white/10 bg-white/5`替代`border-gray-200 bg-white`
- **问题文字**：text-white
- **答案文字**：text-slate-300
- **hover状态**：hover:bg-white/5
- **展开按钮**：`bg-gold-500/10`替代`bg-brand-50`，图标`text-gold-400`替代`text-brand-600`

### 9. CTA区域
- **CTA卡片**：使用金色渐变深色背景（bg-gradient-to-br from-gold-500/10 via-navy-900 to-navy-950），边框`border-gold-500/20`
- **标题**：白色，"腾飞"使用金色
- **描述**：text-slate-300
- **按钮**：
  - 主按钮：`variant="brand"`（金色渐变，navy文字）→ 路由改为`/drama`
  - 次按钮：`variant="secondary"`（白色边框半透明背景）
- 移除`btn-gold`/`btn-primary`等旧class，使用Button组件

### 10. 文案替换
- "Drama Skills 36角色体系" → "Drama Skills 12位专业角色体系"
- 统计数据保持不变（"8大"已正确）
- 检查其他36相关引用（目前只在TESTIMONIALS第2条发现）

### 11. 保持的功能
- `useConfig`读取配置
- `normalizeHeroStats`数据归一化
- framer-motion所有动画（pageEnter, whileInView等）
- THEME_META_LIST和ThemeBadge组件
- renderLucideIcon图标渲染
- PIPELINE流程展示
- FAQ展开/收起交互

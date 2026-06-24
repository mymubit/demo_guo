# 全站页面改造最终一次性完成计划

## 一、项目现状总结

经过前面的重构，目前项目状态如下：

### ✅ 已完成深色主题改造的页面（17个）

**用户端页面：**
1. `/` - 首页 (Home/index.jsx) - 深色影院主题完成
2. `/login` - 登录页 (Auth/Login.jsx + AuthShell.jsx) - 完成
3. `/register` - 注册页 (Auth/Register.jsx) - 完成
4. `/404` - 404页 (NotFound.jsx) - 完成
5. `/drama` - 创作中心列表 (Drama/index.jsx) - 完成
6. `/drama/workspace/:id` - 创作工作台 (Drama/WorkspacePage.jsx) - 完成
7. `/drama/scripts/:id` - 剧本展示页 (Drama/ScriptsPage.jsx) - 完成
8. `/works` - 作品列表 (Works/index.jsx) - 完成
9. `/works/:id` - 作品详情 (Works/Detail.jsx) - 完成
10. `/evaluate` - 剧本评估 (Tools/ScriptEvaluate.jsx + ToolsShell.jsx) - 完成
11. `/pull-sheet` - 拉片分析 (Tools/PullSheetAnalyze.jsx) - 完成
12. `/wallet` - 钱包页面 (Wallet/index.jsx) - 完成
13. `/profile` - 个人中心 (Profile/index.jsx) - 完成
14. `/orders` - 订单页面 (Orders/index.jsx) - 完成
15. `/share/:id` - 分享预览 (Share/index.jsx) - 完成

**布局与基础组件：**
16. MainLayout.jsx - 主站布局（顶栏、移动端菜单、Footer）- 完成
17. AdminLayout.jsx - 管理后台布局（侧边栏、面包屑、顶栏）- 完成
18. PageShell.jsx - 统一页面头部组件 - 完成
19. AdminShell.jsx - 后台页面外壳组件 - 完成
20. UI基础组件库（Button, Card, EmptyState, Tabs, Badge等）- 深色主题完成
21. Dashboard.jsx - 管理后台仪表盘 - 深色主题完成

### ❌ 剩余需完成的页面/模块

**唯一未完成的用户端页面：**
1. **Member/index.jsx - 会员中心页面** - 当前仍为浅色主题（text-gray-900, bg-white, border-gray-200），需要完全重构为深色影院主题

**Admin后台页面验证：**
- Admin后台已统一使用 AdminShell、AdminUI、AdminPrimitives 组件体系
- Dashboard已确认深色主题完成
- 其他Admin页面均基于AdminShell和统一UI组件构建，深色主题自动适配

---

## 二、Member 页面改造详细方案

### 改造目标
将 Member/index.jsx 从浅色主题完全重构为与全站一致的深色影院主题（navy-950背景 + gold金色点缀 + glass态玻璃卡片）。

### 具体改造点

#### 1. 页面容器与标题区
- **当前**：`min-h-screen pt-16 pb-20` + `text-gray-900`
- **改造为**：使用 PageShell 统一页面外壳，`bg-navy-950` 深色背景，标题使用 `text-white` + 金色渐变
- 面包屑/快捷链接改为深色玻璃态按钮

#### 2. 会员状态Hero卡片
- **当前**：浅色背景 + 白色卡片嵌套
- **改造为**：
  - 非会员：`border-white/10 bg-white/[0.04] backdrop-blur-sm` 玻璃态
  - 会员：`border-gold-500/30 bg-gradient-to-br from-gold-500/15 via-navy-900/80 to-navy-950` 金色渐变玻璃态
  - 内部3个统计小卡片全部改为深色玻璃态

#### 3. 权益对比区
- **当前**：白色背景卡片 + 灰色边框
- **改造为**：
  - 普通用户：`border-white/10 bg-white/[0.04]` 玻璃态
  - 会员用户：`border-gold-500/30 bg-gold-500/5` 金色高亮玻璃态
  - 文字颜色改为 text-slate-300 / text-white 体系

#### 4. Tab导航
- **当前**：白色背景 + 灰色边框
- **改造为**：与Wallet/Orders页面一致的金色分段控件风格
  - 激活态：`bg-gradient-to-r from-gold-400 to-gold-500 text-navy-950`
  - 非激活态：`border border-white/10 bg-white/5 text-slate-400 hover:text-white`

#### 5. 套餐选择卡片区
- **当前**：白色卡片 + 浅灰边框
- **改造为**：
  - 普通套餐：`border-white/10 bg-white/[0.04] backdrop-blur-sm`
  - 推荐套餐：`border-gold-500/40 bg-gradient-to-br from-gold-500/10 to-navy-900/50 shadow-gold`
  - 按钮统一使用 Button 组件的 variant="gold"

#### 6. 卡密兑换区
- **当前**：白色表单 + 浅灰边框
- **改造为**：深色玻璃态卡片
  - 输入框：`bg-white/5 border-white/10 text-white placeholder-slate-500 focus:border-gold-500/50`
  - 兑换按钮：统一使用 Button variant="gold"

#### 7. 订单列表区
- **当前**：白色容器
- **改造为**：深色玻璃态卡片，OrdersListPanel 组件已支持深色主题

#### 8. 价格组件适配
- PriceWithDiscount 组件需要确认深色主题下的显示效果，必要时调整 chargeTone 属性

---

## 三、执行步骤（一次性完成）

### 步骤1：改造 Member/index.jsx 会员中心页面
- 移除旧的 PageContainer 和浅色样式
- 引入 PageShell 统一页面头部
- 所有区域改为深色玻璃态 + gold金色主题
- 统一使用 Button 组件替代原生 button
- 输入框、卡片、Tab全部适配深色主题

### 步骤2：构建验证
- 运行 `npm run build` 检查编译错误
- 修复任何类型错误、导入错误或样式问题
- 确保所有页面都能正常编译

### 步骤3：最终验证
- 检查所有页面是否都使用深色主题
- 确认没有遗留的浅色样式（text-gray-900, bg-white 等在非背景区域的使用）
- 确保响应式布局在移动端正常工作

---

## 四、风险与注意事项

1. **PriceWithDiscount 组件**：该组件在 commerce 目录下，需要确认其深色主题表现，如不兼容则微调样式
2. **OrdersListPanel 复用**：该组件已在 Orders 页面深色主题下使用，确认可直接复用
3. **useMyMembership Hook**：数据获取逻辑无需修改，仅改展示层
4. **不破坏业务逻辑**：所有改造仅涉及样式和组件结构，不修改API调用、状态管理、业务流程

---

## 五、完成标准

✅ Member页面完全适配深色影院主题，视觉风格与其他页面100%统一
✅ 所有交互按钮使用统一的Button组件
✅ 卡片、表单、Tab等元素使用glass态深色样式
✅ 项目构建成功，无编译错误
✅ 全站所有页面深色主题改造完成（用户端 + Admin端核心框架）

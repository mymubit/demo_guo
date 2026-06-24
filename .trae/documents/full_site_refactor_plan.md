# 全站页面一次性重构完整计划

## 一、现状梳理

### 已完成重构（深色主题 + 统一设计规范）
| 页面/组件 | 文件路径 | 状态 |
|----------|---------|------|
| PageShell统一页面头部 | `/frontend/src/components/layout/PageShell.jsx` | ✅ 完成 |
| EmptyState空状态组件 | `/frontend/src/components/ui/EmptyState.jsx` | ✅ 完成 |
| Drama创作中心 - 项目列表 | `/frontend/src/pages/Drama/index.jsx` | ✅ 完成 |
| Drama创作中心 - 工作台 | `/frontend/src/pages/Drama/WorkspacePage.jsx` | ✅ 完成 |
| Drama创作中心 - 剧本阅读器 | `/frontend/src/pages/Drama/ScriptsPage.jsx` | ✅ 完成 |
| 我的作品列表 | `/frontend/src/pages/Works/index.jsx` | ✅ 完成 |
| 作品详情页 | `/frontend/src/pages/Works/Detail.jsx` | ✅ 完成 |
| 首页Home | `/frontend/src/pages/Home/index.jsx` | ✅ 已是深色主题 |
| Auth登录/注册/AuthShell | `/frontend/src/pages/Auth/` | ✅ 已是深色主题 |
| NotFound 404 | `/frontend/src/pages/NotFound.jsx` | ✅ 已是深色主题 |
| OrdersListPanel订单列表面板 | `/frontend/src/components/orders/OrdersListPanel.jsx` | ✅ 已是深色主题 |
| AdminShell/AdminLayout后台壳 | `/frontend/src/components/admin/AdminShell.jsx` | ✅ 已是深色主题 |

---

## 二、待重构页面清单（一次性全部完成）

### 第一部分：C端用户页面（浅色→深色统一改造）

#### 1. Wallet钱包页面
- **文件**: `/frontend/src/pages/Wallet/index.jsx`
- **问题**: 完全浅色主题（bg-white、text-gray-900、border-gray-200），使用ConsumerSection浅色组件
- **改造要点**:
  - 使用PageShell统一头部
  - 余额卡片改为金色渐变玻璃态
  - 充值套餐卡片改为深色玻璃态，高亮推荐套餐
  - 流水列表改为深色表格风格
  - 筛选Tab改为深色分段控件
  - 适配移动端布局

#### 2. Profile个人中心
- **文件**: `/frontend/src/pages/Profile/index.jsx`
- **问题**: 完全浅色主题
- **改造要点**:
  - 使用PageShell统一头部
  - 用户信息卡片改为玻璃态，头像+昵称+会员状态
  - Tab切换（资料/账号/统计）改为深色分段控件
  - 表单输入框适配深色主题
  - 创作统计卡片改为玻璃态
  - 保存按钮金色主题

#### 3. Orders订单独立页面
- **文件**: `/frontend/src/pages/Orders/index.jsx`
- **问题**: 外层PageContainer浅色，内部OrdersListPanel已深色
- **改造要点**:
  - 使用PageShell统一头部
  - 筛选PillFilterGroup改为深色分段控件
  - 外层容器适配深色背景
  - 空状态使用统一EmptyState组件

#### 4. Share分享预览页
- **文件**: `/frontend/src/pages/Share/index.jsx`
- **问题**: bg-gray-50 + bg-white 浅色主题
- **改造要点**:
  - 整体改为深色背景navy-950
  - 顶部提示栏玻璃态
  - 剧本内容区玻璃态卡片，prose-invert阅读样式
  - 错误/加载状态适配深色
  - 底部跳转首页CTA按钮金色主题

#### 5. Member会员中心
- **文件**: `/frontend/src/pages/Member/index.jsx`
- **问题**: 大部分浅色，仅部分区域深色
- **改造要点**:
  - 使用PageShell统一头部
  - 会员状态Hero卡片统一为金色渐变玻璃态
  - 权益对比卡片深色玻璃态
  - Tab切换（套餐选择/卡密兑换/我的订单）改为金色激活样式
  - 套餐卡片玻璃态，推荐套餐突出显示
  - 卡密兑换表单深色输入框
  - 所有按钮统一Button组件规范

#### 6. ToolsShell工具页外壳组件
- **文件**: `/frontend/src/components/tools/ToolsShell.jsx`
- **问题**: 完全浅色（bg-white、border-gray-200、bg-gray-50）
- **改造要点**:
  - 左侧导航栏改为深色玻璃态
  - 导航项选中状态金色高亮
  - 右侧工作区背景navy-950
  - 提示信息卡片金色边框玻璃态
  - 整体适配PageShell风格

#### 7. Tools/PullSheetAnalyze拉片分析
- **文件**: `/frontend/src/pages/Tools/PullSheetAnalyze.jsx`
- **问题**: 内容卡片浅色，输入框sf-control浅色
- **改造要点**:
  - 内容卡片改为玻璃态深色
  - label文字改为s late-300
  - textarea输入框适配深色
  - 结果展示区适配深色prose
  - 生成按钮统一金色主题

#### 8. Tools/ScriptEvaluate剧本评估
- **文件**: `/frontend/src/pages/Tools/ScriptEvaluate.jsx`
- **问题**: 内容卡片浅色，下拉选择浅色
- **改造要点**:
  - 作品选择下拉框深色
  - 评估结果卡片玻璃态
  - ScoreReport组件已有深色样式无需修改
  - 整体布局适配深色主题

---

### 第二部分：Admin后台核心页面检查与适配

AdminShell已经是深色，但检查以下核心页面确保内容卡片完全适配：

| 页面 | 文件路径 | 检查要点 |
|------|---------|---------|
| Admin Dashboard | `/frontend/src/pages/Admin/Dashboard.jsx` | 统计卡片、图表区域深色适配 |
| 模型配置 | `/frontend/src/pages/Admin/model/ModelHubPage.jsx` | 表格、表单深色 |
| 会员/订单 | `/frontend/src/pages/Admin/Users.jsx`、`Orders.jsx`、`Members.jsx` | 列表、筛选深色 |
| 创作项目管理 | `/frontend/src/pages/Admin/CreationProjects.jsx` | 项目卡片、追踪页深色 |
| 技能中心 | `/frontend/src/pages/Admin/skills/SkillCenterPage.jsx` | 技能卡片深色 |
| 运营监控 | `/frontend/src/pages/Admin/monitoring/MonitoringDashboardPage.jsx` | 图表、统计卡片 |
| 财务管理 | `/frontend/src/pages/Admin/billing/BillingAdminView.jsx` | 账单表格深色 |

> 注：Admin大部分子组件（AdminPrimitives、AdminUI）已经是深色，仅做快速检查和局部调整，不需要大面积重写。

---

## 三、统一改造规范（所有页面严格遵循）

### 色彩规范
| 元素 | Token |
|------|-------|
| 页面背景 | `bg-navy-950` |
| 卡片背景 | `bg-white/[0.03]` ~ `bg-white/[0.06]` 玻璃态 `backdrop-blur-sm` |
| 卡片边框 | `border-white/5` ~ `border-white/10` |
| 主文字 | `text-white` / `text-slate-100` |
| 正文文字 | `text-slate-300` |
| 辅助文字 | `text-slate-400` / `text-slate-500` |
| 品牌金色 | `text-gold-400` / `bg-gold-500` / 渐变 `from-gold-400 to-gold-600` |
| 主按钮 | `variant="gold"` |
| 次按钮 | `variant="secondary"` |
| 幽灵按钮 | `variant="ghost"` |
| 输入框 | `bg-white/5 border-white/10 text-slate-200 placeholder:text-slate-500` |
| focus环 | `focus:border-gold-500/50 focus:ring-2 focus:ring-gold-500/20` |

### 布局规范
- 统一使用 `PageShell` 组件包裹页面，提供返回/标题/描述/操作按钮
- 容器宽度根据页面类型使用 `maxWidth="xl"` / `"4xl"` / `"7xl"`
- 响应式padding: `px-4 sm:px-6 lg:px-8`
- 卡片圆角统一 `rounded-xl` / `rounded-2xl`
- 间距token: gap-3 / gap-4 / gap-5 / gap-6 / gap-8
- 移动端底部预留 `pb-20 sm:pb-8` 避免被底部导航遮挡

### 组件使用规范
- 页面头部: `<PageShell>` 
- 卡片: `<Card variant="glass">`
- 状态标签: `<Badge tone="gold/success/error/info/warning">`
- 按钮: 统一使用 `<Button>` 组件，禁止手写button样式
- 空状态: 统一使用 `<EmptyState>` 组件
- 输入框: 统一深色样式class

---

## 四、执行步骤（按顺序一次性完成）

1. **改造ToolsShell工具页外壳** → 2个工具页（拉片分析、剧本评估）
2. **改造Wallet钱包页**
3. **改造Profile个人中心**
4. **改造Orders订单页**
5. **改造Share分享页**
6. **改造Member会员中心**（页面最大，功能最多）
7. **快速检查Admin核心页面**，修复局部浅色问题
8. **执行 `npm run build` 构建验证**，确保所有页面编译通过
9. **修复所有编译错误/样式问题**

---

## 五、风险与注意事项

1. **不破坏业务逻辑**：仅修改样式className和布局结构，不改动API调用、业务逻辑、状态管理
2. **复用现有组件**：优先使用已重构好的Button/Card/Badge/PageShell/EmptyState，不新增重复组件
3. **保持响应式**：所有页面确保移动端正常显示
4. **删除36角色旧设计**：如果在页面中发现36角色的旧设计直接删除，替换为12角色
5. **无新增依赖**：不引入新的第三方库
6. **构建验证**：最后必须通过完整构建，exit code 0

---

## 六、预期成果

- C端用户流程**所有页面**100%统一深色主题，视觉风格一致
- 从首页→登录→会员→创作→作品→钱包→订单→个人中心→工具，全流程体验统一
- 信息层级清晰，操作按钮权重明确
- 响应式适配完善，移动端体验流畅
- 构建一次通过，无编译错误

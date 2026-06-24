# ScriptForge 全站UI重设计与角色体系清理计划

## 一、仓库现状分析

### 1.1 已完成部分（基于上一轮迭代）
- ✅ 设计令牌：`tailwind.config.js` 已更新为 Deep Navy + Warm Gold 深色电影工业主题
- ✅ 全局样式：`globals.css` 已配置深色基础、噪点背景、滚动条、工具类
- ✅ 核心组件：Button/Card/Badge/BrandLogo 已适配深色主题
- ✅ 布局系统：MainLayout（C端顶栏/页脚）、AdminLayout（后台侧边栏）已重设计
- ✅ 关键页面：Home（首页）、Auth（登录/注册）、NotFound（404）、Drama/index（创作入口）已深色化
- ✅ Admin Dashboard：运营仪表盘已完成深色适配

### 1.2 待完成工作
#### A. 核心创作页面（浅色 → 深色）
- **Drama/WorkspacePage.jsx**：工作台主页面（角色选择/执行/详情），当前为完整浅色主题
- **Drama/ScriptsPage.jsx**：剧本展示/质量报告页，当前为完整浅色主题
- 涉及组件：DramaPresentation、creation/workspace 下的所有子组件

#### B. 后台管理页面（样式对齐）
需要统一深色风格的页面：
- Admin/Users.jsx（用户管理）
- Admin/Members.jsx（会员管理）
- Admin/Orders.jsx（订单管理）
- Admin/Billing.jsx（计费管理）
- Admin/Settings.jsx（设置）
- Admin/CreationProjects.jsx / CreationCenterPage.jsx（创作项目）
- Admin/agent/*（Agent中心相关页面）
- Admin/model/*（大模型配置）
- Admin/billing/*（计费配置）
- Admin/library/AdminLibrary.jsx（知识库）
- Admin/evolution/AdminEvolution.jsx（迭代日志）
- Admin/monitoring/MonitoringDashboardPage.jsx（监控）
- Admin/operations/*（运营工具）
- Admin/skills/*（技能中心）
- Admin/system/*（系统配置）
- Admin/tier-rules/*（分级规则）
- Admin/drama-models/index.jsx（Drama模型配置）
- Admin/portal/*（门户内容配置）

#### C. C端其他页面
- Member/index.jsx（会员页）
- Orders/index.jsx（订单页）
- Profile/index.jsx（个人中心）
- Wallet/index.jsx（钱包页）
- Works/index.jsx + Works/Detail.jsx（作品列表/详情）
- Tools/PullSheetAnalyze.jsx + Tools/ScriptEvaluate.jsx（工具页）
- Share/index.jsx（分享页）

#### D. UI组件库补全
需要深色适配的组件：
- Input/FormControls（表单控件）
- Modal/Drawer（弹窗/抽屉）
- Pagination（分页）
- EmptyState（空状态）
- MetricCard（指标卡）
- Skeleton（骨架屏）
- UserAvatar（头像）
- ThemeBadge（主题徽章）
- StepStatusMark（步骤状态）
- GlobalRequestLoading（全局加载）
- 以及 charts 图表主题

#### E. 角色体系彻底清理（不向后兼容）
**后端清理：**
- `backend/apps/drama/defaults.py`：
  - 删除注释中"36个角色完整定义"、"其余23个旧角色标记 hidden=True"等遗留表述
  - 删除 tier=3 相关配置（TIER_CONFIG 中 tier 3 的定义、隐藏逻辑）
  - 明确 DRAMA_ROLE_DEFAULTS 只保留12个角色定义，彻底删除其他24个旧角色
  - 更新 DRAMA_DEPARTMENTS 为实际使用的5-8个部门
  - 删除 get_roles_by_dept 中的 hidden 过滤逻辑
- `backend/apps/drama/constants.py`：检查并清理36角色相关常量
- `backend/apps/drama/management/commands/seed_drama_skills.py`：更新种子脚本只初始化12个角色
- `backend/apps/agent/independent_defaults.py`：清理旧角色默认值
- `backend/apps/agent/definition_service.py`：移除旧角色兼容逻辑
- 数据库迁移：考虑清理数据库中已存在的 tier=3 角色数据（或标记为废弃）

**前端清理：**
- 删除所有"36个角色"、"三十六"、"36.*role"等文案引用（涉及20+文件）
- WorkspacePage 中删除 tier=3 相关视图和配置（TIER_CONFIG 第3层、TierView中的tier 3折叠逻辑）
- 所有页面统一"12个专业角色"、"8个核心快速通道 + 4个复合增强"表述
- 删除旧的部门配置，对齐后端5-8部门架构
- `frontend/src/utils/agentExecutionLabels.js`、`frontend/src/utils/agentTerm.js`：清理旧角色标签映射

**文档清理（非代码但需统一）：**
- AGENTS.md：更新为12角色描述
- README.md：更新角色数量说明
- drama-skills/ 目录下文档：ROLE-DESIGN-ANALYSIS.md 等需更新（注：用户要求不向后兼容，旧文档标记归档）

## 二、设计规范统一

### 2.1 色彩体系（唯一真实来源）
```css
/* 背景层级 */
--sf-bg: #0a0e1a;           /* 页面底色 Deep Navy */
--sf-surface: rgba(255,255,255,0.04);  /* 卡片表面 */
--sf-surface-elevated: rgba(255,255,255,0.08); /* 悬浮/高亮表面 */
--sf-border: rgba(255,255,255,0.08);   /* 常规边框 */
--sf-border-strong: rgba(255,255,255,0.15); /* 强边框 */

/* 文字层级 */
--sf-text: #f1f5f9;         /* 主文字 */
--sf-text-secondary: #94a3b8; /* 次要文字 */
--sf-text-muted: #64748b;   /* 弱化文字 */

/* 品牌色 */
--sf-brand: #f4b719;        /* Warm Gold 主色 */
--sf-brand-gradient: linear-gradient(135deg, #fcd34d 0%, #f4b719 50%, #d97706 100%);

/* 语义色（深色适配） */
--sf-success: #10b981;
--sf-warning: #f59e0b;
--sf-danger: #ef4444;
--sf-info: #3b82f6;
```

### 2.2 组件样式统一规则
所有页面必须遵循：
1. 页面背景：`bg-navy-950` 加噪点纹理（已在globals.css）
2. 卡片容器：使用 `<Card>` 组件，默认 `sf-glass` 玻璃态效果
3. 按钮：主要操作用 `variant="brand"`（金色渐变），次要用 `variant="secondary"`（透明边框）
4. 文字颜色：主文字 `text-slate-100`/`text-white`，次要 `text-slate-400`，禁用 `text-slate-600`
5. 边框：`border-white/10` 为主，高亮用 `border-gold-500/30`
6. 输入框：`bg-white/5 border-white/10 focus:border-gold-500/50 focus:ring-gold-500/20`
7. 悬停状态：`hover:bg-white/[0.08]` 为基准
8. 渐变强调：Hero区域/欢迎横幅可用金色渐变背景 `bg-gradient-to-br from-gold-600/20 via-navy-900 to-navy-950`

### 2.3 角色展示规范
- 角色分层：只有两层（核心必需 tier=1 + 增强复合 tier=2），**彻底删除 tier=3 专项层**
- 核心必需：8个快速通道角色（⚡标识，金色调）
- 增强复合：4个整合角色（◈标识，青金/强调色调）
- 部门：8个部门（战略选题/世界构建/剧情引擎/创作执行/评审质控/修改润色/制作宣发/合规总编室）
- 统一表述："12个专业短剧创作角色"，"8个核心角色一键走通快速通道"，"4个复合增强角色按需深度定制"

## 三、实施步骤（按依赖顺序）

### Phase 1：底层补全与角色清理（基础层）
**目标**：清理旧角色体系，补全深色UI组件库，为后续页面改造打基础

1. **后端角色彻底清理**
   - 文件：`backend/apps/drama/defaults.py`
   - 操作：
     - 删除文件中除12个可见角色外的所有其他角色定义（只保留DRAMA_ROLE_DEFAULTS中12个角色）
     - 删除 DRAMA_FAST_TRACK_ROLES 之外的tier配置，移除所有 hidden=True 逻辑
     - 更新注释：删除所有"36个角色"、"23个旧角色"、"tier3隐藏"等内容
     - 更新模块docstring为"Drama Skills 12个角色的默认定义"
     - 简化辅助函数：get_visible_roles 直接返回全部，get_roles_by_dept 移除hidden过滤

2. **后端其他文件角色清理**
   - `backend/apps/drama/management/commands/seed_drama_skills.py`：更新种子数据只处理12角色
   - `backend/apps/agent/independent_defaults.py`：清理旧角色定义
   - `backend/apps/agent/definition_service.py`：移除旧角色兼容分支
   - 检查 serializers.py、services.py、views.py：确认不依赖旧角色结构

3. **前端文案与配置清理**
   - 全局搜索"36"、"三十六"、"36.*role"、"tier.*3"、"专项"、"23个"关键词
   - 逐文件清理：
     - `frontend/src/utils/agentExecutionLabels.js`
     - `frontend/src/utils/agentTerm.js`
     - `frontend/src/pages/Admin/drama-models/index.jsx`
     - `frontend/src/pages/Admin/agent/AdminAgentCatalogPanel.jsx`
     - `frontend/src/pages/Admin/CreationProjects.jsx`
     - `frontend/src/pages/Admin/CreationCenterPage.jsx`
     - `frontend/src/components/admin/ProjectAgentTrace.jsx`
     - `frontend/src/components/admin/ai-config/aiConfigSections.jsx`
     - 以及其他匹配文件
   - 统一替换为12角色表述，删除所有tier 3相关分支

4. **UI组件库深色适配补全**
   - `frontend/src/components/ui/FormControls.jsx`（Input/Select/Textarea等）：深色样式
   - `frontend/src/components/ui/Modal.jsx` + `Drawer.jsx`：玻璃态深色弹窗
   - `frontend/src/components/ui/Pagination.jsx`：深色分页
   - `frontend/src/components/ui/EmptyState.jsx`：深色空状态
   - `frontend/src/components/ui/MetricCard.jsx`：深色指标卡
   - `frontend/src/components/ui/Skeleton.jsx`：深色骨架
   - `frontend/src/components/ui/StepStatusMark.jsx`：深色步骤标记
   - `frontend/src/components/charts/theme.js`：ECharts 深色主题配置（金色系）
   - 创建 `Input.jsx` 单独组件（如尚未提取）

**验收标准**：
- 后端 defaults.py DRAMA_ROLE_DEFAULTS 长度为12
- 前端全局搜索无"36个角色"相关表述（文档除外）
- 所有基础UI组件在深色背景下可见、可用、交互正常
- `npm run build` 无组件引用错误

---

### Phase 2：Drama核心创作页面深色重设计（核心业务层）
**目标**：工作台和剧本页这两个最高频使用页面完成电影级深色适配

1. **WorkspacePage.jsx 完整重写**
   - 侧边栏（左侧角色面板）：
     - 背景：`bg-navy-900/80 backdrop-blur-xl` 玻璃态
     - 项目头部：金色渐变高亮区，进度条改为金色
     - 视图切换（分层/部门/快速通道）：深色tab样式，选中态金色
     - 角色列表项：悬停 `hover:bg-white/5`，选中态 `bg-gold-500/10 border-l-2 border-gold-500`
     - 删除 TierView 中 tier=3 的分组和折叠逻辑
     - TIER_CONFIG 只保留 tier1/tier2，删除 tier3 配置
   - 主区域 WelcomePanel：
     - Hero横幅：深色金色渐变背景（替代原brand-600渐变）
     - HeroStat 卡片：玻璃态 `bg-white/5 backdrop-blur border-white/10`
     - 卡片：全部改为深色玻璃Card
     - Step/步骤指示器：深色适配
     - 核心执行路径按钮组：深色悬停态
     - 删除"角色架构说明"中任何36相关表述，明确写"12个角色 = 8核心 + 4复合"
   - RoleDetailPanel：
     - 卡片头部：深色渐变 `from-navy-900/80 to-navy-950/60`
     - 输入/输出依赖区：`bg-white/[0.03] border-white/5`
     - 批量配置卡片：深色accent样式（替代accent-50浅色）
     - 执行输出区：深色代码/内容展示
   - 反馈Toast：确认Sonner已配置深色主题

2. **ScriptsPage.jsx 完整重写**
   - 顶部sticky栏：`bg-navy-900/90 backdrop-blur-xl border-b border-white/10`
   - 侧边分集导航：深色Card，选中项 `bg-gold-500/10 border-l-2 border-gold-500`
   - GRADE_CONFIG：全部改为深色半透明背景（如S级：`bg-gold-500/10 border-gold-500/30 text-gold-300`）
   - SEVERITY_CONFIG：错误/警告/建议的深色背景色
   - ScriptView：
     - 剧本内容卡：深色背景 `bg-navy-900/50`，字体适配深色（剧本头用金色，角色名用强调色，△动作指令用 slate-400）
     - 复制/问题按钮：深色样式
     - SuggestionsPanel：建议列表面板深色化
   - QualityReport：
     - Tab栏：深色tab，选中态金色下划线
     - 雷达图 RadarChart：背景深色，网格线 slate-700，填充 gold/20，描边 gold-400
     - 维度卡片：深色玻璃Card，进度条金色
     - 情绪曲线 EmotionCurve：深色SVG背景
     - SummaryReport：所有状态块深色适配
   - DIM_META 颜色更新为深色可见的金色/翡翠色等

3. **Drama 相关子组件适配**
   - `components/drama/presentation/DramaPresentation.jsx`：产物展示组件深色适配
   - `components/creation/workspace/*`：所有workspace子组件深色样式检查和更新

**验收标准**：
- WorkspacePage 从进入到角色执行全流程无浅色元素
- ScriptsPage 剧本阅读、质量报告tab切换无浅色突兀
- 删除所有tier 3/专项角色相关UI入口
- 12角色展示正确：8核心+4复合
- 文字对比度达标（主次文字清晰可辨）
- 核心功能（执行角色、查看剧本、查看质量报告）交互正常

---

### Phase 3：Admin后台全页面样式对齐（管理后台层）
**目标**：所有后台管理页面统一深色电影工业风格，与Dashboard保持一致

**策略**：AdminLayout 已提供深色基础框架，主要工作是替换页面内遗留的浅色类名（如 `bg-white`、`text-slate-900`、`border-slate-200`、`bg-slate-50`等）

按模块批量处理：

1. **基础管理页面（优先级高）**
   - Dashboard.jsx（已完成，作为样式基准）
   - Users.jsx → 用户列表/详情深色化
   - Members.jsx + MemberSettingsRoute.jsx → 会员管理深色化
   - Orders.jsx + OrdersListPanel.jsx + OrderStatusBadge.jsx → 订单系统深色化
   - Billing.jsx + billing/* → 计费配置深色化
   - Settings.jsx → 系统设置深色化

2. **创作与项目管理**
   - CreationCenterPage.jsx → 创作中心首页
   - CreationProjects.jsx → 项目列表
   - CreationProjectTrace.jsx → 项目轨迹
   - ProjectSpotlightCard.jsx、ProjectOpsSummary.jsx 等子组件

3. **Drama模型配置**
   - drama-models/index.jsx → 模型配置+Token统计
   - 确保页面内所有表格、表单、按钮符合深色规范
   - 删除36角色相关文案

4. **Agent与模型配置**
   - agent/AgentHubPage.jsx
   - agent/AdminAgentCatalogPanel.jsx
   - agent/AgentRunsPanel.jsx
   - agent/AgentLlmRoutePanel.jsx
   - agent/IndependentAgentPanel.jsx
   - agent/AgentConfigEditors.jsx
   - agent/AdminAgentPromptEditor.jsx
   - agent/AdminAgentKindBadge.jsx
   - model/ModelHubPage.jsx + model目录下所有配置组件
   - AdminPrimitives.jsx、AdminShell.jsx、AdminMasterDetail.jsx 等基础admin组件检查

5. **知识库、迭代、监控**
   - library/AdminLibrary.jsx
   - evolution/AdminEvolution.jsx
   - monitoring/MonitoringDashboardPage.jsx
   - ExecutionRunPanel.jsx（共享执行详情面板）

6. **运营、技能、系统配置**
   - operations/* 所有运营工具页面
   - skills/* 技能中心页面
   - system/* 系统配置页面
   - tier-rules/* 分级规则页面
   - portal/* 门户内容配置

7. **Admin通用组件检查**
   - AdminUI.jsx（AdminPageHeader/AdminLoading/AdminMessage/AdminStatGrid/AdminTabBar）确认深色样式完整
   - DashboardOpsActionCards.jsx
   - AgentTimelineCard.jsx
   - OrchestrationDraggableList.jsx
   - SubSkillStepBar.jsx
   - charts/* 所有图表组件深色主题统一

**验收标准**：
- 侧边栏导航进入任一Admin页面，视觉风格与Dashboard一致
- 表格、表单、按钮、弹窗、tab、分页等所有控件深色化
- 数据可视化图表颜色适配深色背景
- 无大面积纯白/浅灰背景块
- 所有管理功能操作正常

---

### Phase 4：C端其他页面深色化（用户前端层）
**目标**：用户侧所有页面统一深色体验

1. **会员与订单**
   - Member/index.jsx → 会员开通/权益页
   - Orders/index.jsx → 我的订单
   - Wallet/index.jsx → 钱包/充值页
   - WalletBadge.jsx → 钱包徽章组件

2. **个人与作品**
   - Profile/index.jsx → 个人中心
   - Works/index.jsx → 作品列表
   - Works/Detail.jsx → 作品详情
   - WorkMetaPanel.jsx、WorkVisualizationSection.jsx 等作品子组件

3. **工具页**
   - Tools/PullSheetAnalyze.jsx → 拉片分析
   - Tools/ScriptEvaluate.jsx → 剧本评估
   - ToolsShell.jsx

4. **分享页**
   - Share/index.jsx → 分享落地页

5. **共享C端组件**
   - ConsumerSection.jsx
   - ConsumerErrorBoundary.jsx
   - billing/WalletBadge.jsx
   - commerce/PriceWithDiscount.jsx
   - orders/OrdersListPanel.jsx 等

**验收标准**：
- 用户从首页→登录→创作→查看作品→会员中心全流程深色体验一致
- 无页面跳转让用户感觉"进入了另一个网站"
- 所有按钮、卡片、表单风格统一

---

### Phase 5：构建验证与细节打磨（验收层）

1. **全量构建与类型检查**
   ```bash
   cd /workspace/frontend
   npm run build
   ```
   - 解决所有构建错误、警告
   - 清理未使用的import和变量
   - 检查控制台无React warning（key缺失、依赖数组等）

2. **遗留浅色扫描**
   - 全局搜索危险浅色类名，确认只在必要处使用：
     - `bg-white` → 应该改为 `bg-white/5`、`bg-navy-900`、`glass`等，除非是特别高亮
     - `text-slate-900`/`text-gray-900` → 主文字应为 `text-slate-100`/`text-white`
     - `bg-slate-50`/`bg-gray-50` → 应为 `bg-white/[0.03]`
     - `border-slate-200`/`border-gray-200` → 应为 `border-white/10`
   - 逐个确认剩余浅色类名是否有存在合理性（如特别强调的toast内部等）

3. **角色文案最终校验**
   - 全局确认：
     - 无"36个角色"、"三十六"、"36 roles"表述（docs/archive可例外）
     - 无tier=3、"专项"角色分组UI
     - 统一为"12个专业角色"、"8个核心快速通道"、"4个复合增强角色"

4. **交互体验检查清单**
   - 所有按钮有hover/active状态
   - 所有可点击元素cursor-pointer
   - 表单输入focus态有金色高亮
   - 加载状态、空状态、错误状态样式统一
   - 弹窗/抽屉有正确backdrop和关闭动画
   - 滚动条样式统一（细、深色、金色hover）
   - 响应式布局在桌面/平板/移动端均可正常使用

5. **启动开发服务器做视觉走查**
   ```bash
   npm run dev
   ```
   - 逐一访问所有路由页面截图对比
   - 检查核心流程：注册→登录→创建Drama项目→工作台执行→查看剧本→质量报告
   - 检查后台所有菜单页面

**验收标准**：
- `npm run build` 成功，无error
- 所有路由可访问，无JS运行时错误
- 视觉风格全站统一
- 核心业务流程可用
- 无遗留36角色/tier3相关内容

## 四、涉及文件清单（汇总）

### 后端文件
- `backend/apps/drama/defaults.py`（核心清理）
- `backend/apps/drama/management/commands/seed_drama_skills.py`
- `backend/apps/drama/constants.py`
- `backend/apps/agent/independent_defaults.py`
- `backend/apps/agent/definition_service.py`

### 前端核心页面
- `frontend/src/pages/Drama/WorkspacePage.jsx`（重写）
- `frontend/src/pages/Drama/ScriptsPage.jsx`（重写）
- `frontend/src/pages/Drama/index.jsx`（复查微调）

### 前端Admin页面（约30+文件）
- Dashboard、Users、Members、Orders、Billing、Settings系列
- Creation* 系列
- agent/*、model/*、billing/*、library/*、evolution/*、monitoring/*
- operations/*、skills/*、system/*、tier-rules/*、drama-models/*、portal/*

### 前端C端页面
- Member/、Orders/、Profile/、Wallet/、Works/、Tools/、Share/ 目录下index.jsx

### 前端组件
- ui/ 下所有组件（补全深色样式）
- admin/ 下所有组件（样式统一）
- creation/、drama/、billing/、commerce/、orders/、works/、charts/、shared/ 下组件检查
- layout/MainLayout.jsx、AdminLayout.jsx（复查）

### 前端配置/工具
- tailwind.config.js（微调如需）
- styles/globals.css（补全工具类如需）
- utils/agentExecutionLabels.js、utils/agentTerm.js（角色标签清理）
- config/adminNav.js、config/consumerNav.js（如有角色相关描述更新）

## 五、风险与应对

1. **风险**：页面过多，逐页改容易漏
   **应对**：先做组件层→再做高频核心页（Drama工作台/剧本）→再批量处理Admin→最后C端其他页，每Phase完成后构建验证

2. **风险**：深色背景下文字对比度不足
   **应对**：严格遵循色彩体系：主文字#f1f5f9，次要#94a3b8，弱化#64748b，避免用slate-300以下做主文字

3. **风险**：删除旧角色导致历史数据兼容问题
   **应对**：用户明确要求"不向后兼容"，数据库中旧tier3角色历史记录保留数据，但前端不展示、不提供入口；后端API不主动返回hidden角色（get_visible_roles直接返回12个）

4. **风险**：ECharts图表深色主题不统一
   **应对**：集中在 `components/charts/theme.js` 统一配置图表配色，所有图表共用主题

5. **风险**：Tailwind类名批量替换误改
   **应对**：不做全局批量替换，逐组件逐页面阅读上下文后修改；每修改完一个模块立即构建检查

## 六、成功标准

项目最终达到：
1. **视觉统一**：全站（C端+后台）采用一致的Deep Navy + Warm Gold深色电影工业风格，玻璃态质感，无割裂感
2. **角色正确**：系统中彻底删除36角色设计，只保留12个角色（8核心+4复合），所有界面文案、数据结构、种子脚本统一
3. **体验升级**：核心创作流程（工作台、剧本阅读、质量报告）视觉专业感明显提升，达到"电影级专业创作工具"质感
4. **代码干净**：构建无错误，控制台无警告，无遗留旧代码、无兼容分支、无死代码
5. **可用完整**：所有原有功能正常可用，只是UI变好看，无功能回归

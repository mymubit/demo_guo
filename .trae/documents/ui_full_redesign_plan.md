# ScriptForge · 项目级 UI 全面重构计划

## 仓库调研结论

### 现状分析
经过代码库全面调研，当前项目存在以下核心问题：

1. **设计系统割裂**：三套视觉语言混用
   - C 端主站：浅色背景 + indigo (#6366f1) 品牌色
   - Admin 后台：深色 navy + gold 配色（较成熟）
   - Drama 创作模块：部分用浅色、部分混用深色，风格不统一
   - Toaster 设置为 dark 主题但 CSS 写的是浅色 toast 样式

2. **老设计残留（需彻底删除，不向后兼容）**
   - [defaults.py](file:///workspace/backend/apps/drama/defaults.py) 文件头注释仍写"36个角色"
   - [Home/index.jsx](file:///workspace/frontend/src/pages/Home/index.jsx) 用户评价提到"Drama Skills 36角色体系"
   - [Home/index.jsx](file:///workspace/frontend/src/pages/Home/index.jsx) PIPELINE 展示是 7 步，与实际 12 角色工作流不符
   - 部分遗留 CSS 类 (btn-gold/btn-primary 等) 与组件库 Button 并存

3. **视觉品质问题**
   - 首页 Hero 区过于普通，缺乏电影/创作行业的专业感
   - Drama 创作入口页（DramaIndex）信息密度高但视觉层次弱
   - 组件使用不统一，部分页面仍用原生 HTML + 自定义 CSS 类
   - 空状态、加载态、错误态表现不一致
   - 缺少微交互动效和品牌个性

4. **实际角色现状（已确认）**
   - 当前系统实际为 **12 个角色**：8 个快速通道核心角色 + 4 个专家通道增强角色
   - 分为 8 个职能部门（战略选题→世界构建→剧情引擎→创作执行→评审质控→修改润色→制作宣发→合规总编室）
   - `defaults.py` 中 `DRAMA_VISIBLE_ROLES` 已正确配置为 12 个，无需改动业务逻辑
   - 仅需清理文案/注释中残留的"36角色"表述

### 设计方向决策

**美学方向：电影工业级专业创作工具**
- **主色调**：深海军蓝 (Deep Navy #0a0e1a) + 暖金 (Warm Gold #f4b719) 作为品牌主色，替代原有 indigo
- **气质定位**：专业、沉浸、电影感、值得信赖——类似 DaVinci Resolve / Final Cut Pro 等专业创作工具的质感
- **C 端展示**：深色电影感 Hero + 精致卡片，突出"AI编剧团队"概念
- **创作工作台**：沉浸式深色界面，降低视觉疲劳，适合长时间创作
- **Admin 后台**：保持深色专业感，优化信息密度和操作效率
- **字体**：中文使用"思源黑体"体系，英文标题使用有电影感的衬线/无衬线字体

## 需要修改的文件与模块

### 设计系统核心（6 个文件）
- [tailwind.config.js](file:///workspace/frontend/tailwind.config.js) - 更新色板、字体、阴影、圆角
- [globals.css](file:///workspace/frontend/src/styles/globals.css) - 更新设计令牌、基础样式、自定义组件
- [Button.jsx](file:///workspace/frontend/src/components/ui/Button.jsx) - 统一按钮变体
- [Card.jsx](file:///workspace/frontend/src/components/ui/Card.jsx) - 统一卡片样式
- [Badge.jsx](file:///workspace/frontend/src/components/ui/Badge.jsx) - 统一徽章样式
- [BrandLogo.jsx](file:///workspace/frontend/src/components/ui/BrandLogo.jsx) - 升级 Logo 视觉

### 布局层（3 个文件）
- [MainLayout.jsx](file:///workspace/frontend/src/components/layout/MainLayout.jsx) - 全新顶栏+页脚，统一导航
- [AdminLayout.jsx](file:///workspace/frontend/src/components/layout/AdminLayout.jsx) - 优化侧边栏视觉
- [App.jsx](file:///workspace/frontend/src/App.jsx) - Toast 主题与全局样式对齐

### C 端页面（5 个文件）
- [Home/index.jsx](file:///workspace/frontend/src/pages/Home/index.jsx) - 首页全面重设计
- [consumerNav.js](file:///workspace/frontend/src/config/consumerNav.js) - 导航配置更新
- [Drama/index.jsx](file:///workspace/frontend/src/pages/Drama/index.jsx) - 创作入口页重设计
- [NotFound.jsx](file:///workspace/frontend/src/pages/NotFound.jsx) - 404 页面优化
- [Auth/Login.jsx](file:///workspace/frontend/src/pages/Auth/Login.jsx) + [Register.jsx](file:///workspace/frontend/src/pages/Auth/Register.jsx) - 登录注册页统一风格

### Drama 工作台（2 个文件）
- [WorkspacePage.jsx](file:///workspace/frontend/src/pages/Drama/WorkspacePage.jsx) - 工作台界面优化（基于现有组件升级）
- [ScriptsPage.jsx](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx) - 剧本展示页优化

### Admin 后台（2 个文件）
- [adminNav.js](file:///workspace/frontend/src/config/adminNav.js) - 导航项检查清理
- [drama-models/index.jsx](file:///workspace/frontend/src/pages/Admin/drama-models/index.jsx) - 与新设计系统对齐

### 后端文案清理（2 个文件）
- [defaults.py](file:///workspace/backend/apps/drama/defaults.py) - 更新文件头注释，移除 36 角色表述
- （前端文案已在上述页面中处理）

## 修改步骤

### 阶段一：设计系统重构（核心基础）

#### 步骤 1：更新 Tailwind 配置与设计令牌
- 将主品牌色从 indigo (#6366f1) 改为 **深海军蓝 + 暖金** 双主色体系
  - navy: 50→950 色阶（主背景、文字、UI 容器）
  - gold/accent: 50→600 色阶（CTA、强调、品牌高亮）
  - 保留 slate 系作为中性色，但加深暗部色阶
  - 语义色（success/warning/danger/info）微调以适配深色主题
- 字体配置：
  - 标题字体：`'Noto Serif SC', 'Source Han Serif SC', serif`（中文衬线，电影海报感）
  - 正文字体：`'Inter', 'Noto Sans SC', system-ui, sans-serif`
  - 等宽字体：`'JetBrains Mono', monospace`（代码/数据展示）
- 扩展设计令牌：
  - 阴影：soft/medium/strong/dramatic 四级
  - 圆角：sm/md/lg/xl/2xl（保持现有，增加 card 专用圆角）
  - backdrop-blur 值统一
- 配置 `darkMode: 'class'` 以便未来支持明暗切换（首期全部使用深色主题风格）

#### 步骤 2：重写 globals.css
- 更新 `:root` CSS 变量为 navy+gold 体系
- 浅色 C 端页面改为 **深色电影风格**（主背景 #0a0e1a，不是纯白）
- 删除遗留的 `.btn-gold` / `.btn-primary` / `.btn-ghost` / `.gradient-text` 等老 CSS 类
- 删除 `.sf-surface-card` / `.sf-feature-card` / `.sf-console-panel` 等遗留类，改用 Tailwind
- 更新 Sonner toast 样式为深色主题，与 App.jsx 的 `theme="dark"` 一致
- 优化滚动条样式，匹配深色主题
- 添加电影感的背景噪点纹理（subtle noise overlay）
- 添加页面入场动画的基础 CSS keyframes

#### 步骤 3：统一 UI 基础组件
- **Button 组件**：
  - variant: `primary`（金底深字，主CTA）、`secondary`（透明描金边，次按钮）、`ghost`（无背景悬停效果）、`danger`
  - size: sm/md/lg
  - 统一 loading 态、disabled 态、icon 间距
  - 添加 hover 时的微妙上移 + 发光效果
- **Card 组件**：
  - variant: `default`（深色半透明白色描边）、`elevated`（带阴影）、`interactive`（可悬停上浮+发光）
  - 统一 padding 规范
  - 玻璃拟态效果用于重要卡片
- **Badge 组件**：
  - tone 重新映射：brand(gold)/success/warning/danger/info/default
  - 统一大小和圆角
- **BrandLogo 组件**：
  - 深色背景适配
  - 增加 Logo 动画效果（初次加载时）
  - 统一 consumer/admin 两种变体的视觉语言

### 阶段二：布局层重构

#### 步骤 4：重写 MainLayout（C 端主布局）
- 顶栏改为**深色半透明毛玻璃**（bg-navy-900/80 backdrop-blur-xl），边框色用白色/5
- 导航项激活态改为金色高亮 + 左侧/底部金色指示条
- 用户菜单下拉改为深色背景，金色hover态
- 登录/注册按钮使用金色主按钮样式
- 页脚改为深色背景（bg-navy-950），文字用 navy-200/400 层级
- 移动端菜单适配深色主题
- 顶栏滚动时增加微妙阴影增强
- 移除 footer 中未实现的"使用教程/创作指南/常见问题"无效链接

#### 步骤 5：优化 AdminLayout
- 侧边栏背景色与主区域更协调（减少渐变复杂度）
- 侧边栏激活项的金色指示条优化为更精致的形态
- 用户信息卡片视觉优化
- 面包屑样式与新设计系统对齐
- 顶栏右侧增加快速返回 C 端的入口
- 主内容区背景微调，增加微妙的径向渐变光效

#### 步骤 6：更新 App.jsx
- Toast 配置与新深色 CSS 对齐
- 确认 toast 样式类名正确对应

### 阶段三：C 端页面重设计

#### 步骤 7：首页（Home）全面重设计
这是本次重构的视觉重点：

- **Hero 区域**：
  - 全屏电影感深色背景（使用生成的电影剪辑室/剧本场景图）
  - 背景添加多层渐变叠加（顶部暗化 vignette，底部过渡到页面底色）
  - 主标题：大号衬线字体，金色渐变文字效果
  - 副标题：克制的说明文案，描述"你的专属AI编剧团队"
  - 双 CTA："开始创作"（金色主按钮）+ "查看演示"（透明次按钮）
  - 下方统计数字：使用等宽字体，金色数字 + 白色标签
  - 添加微妙的粒子/光线动画效果

- **12 角色展示区**（替代旧的FEATURES/PIPELINE）：
  - 标题："12 位专业角色，组成你的专属编剧团队"
  - 8 个部门 × 12 个角色，用部门分组展示
  - 每个角色卡片：部门色标识 + 中文名 + 英文名 + 一句话职责
  - 快速通道 8 角色 vs 专家通道增强 4 角色的视觉区分
  - 卡片悬停时有上浮 + 金色发光效果

- **创作流程展示**（替代旧 PIPELINE）：
  - 正确展示 8 阶段创作流程（战略选题→世界构建→剧情引擎→创作执行→评审质控→修改润色→制作宣发→合规审查）
  - 水平时间线样式，金色节点连接
  - 每阶段标注负责角色

- **功能特性区**：
  - 保留但重新设计 6 个特性卡片
  - 深色玻璃拟态卡片，图标用金色
  - 布局改为不对称网格增加设计感

- **用户评价区**：
  - 修复文案：删除"36角色体系"表述，改为"12角色专业体系"
  - 评价卡片改为深色风格，金色星级评分
  - 添加引用符号装饰

- **FAQ 区**：
  - 折叠式交互，深色风格
  - 展开/收起动画

- **CTA 收尾区**：
  - 大色块金色强调，引导注册/开始创作

#### 步骤 8：Drama 创作入口页（DramaIndex）重设计
- 顶部 Header 改为深色风格（与首页统一）
- 页面背景从 bg-slate-25 改为深色 bg-navy-950
- "快速通道" vs "专家通道"两个入口卡片：
  - 改为深色玻璃拟态卡片
  - 增加通道的角色数量、适用场景、包含阶段的可视化
  - 选中态有金色边框发光
- 新建项目 Modal：
  - 深色风格表单
  - 题材矩阵选择改为更直观的标签式交互
  - 创新组合推荐增加热度标识
  - 输入框聚焦态改为金色边框
- 项目列表卡片：
  - 深色卡片风格
  - 进度条使用金色渐变
  - 质量评级徽章颜色适配深色主题
  - 卡片悬停上浮效果

#### 步骤 9：登录/注册页统一风格
- 全屏深色背景，与整体风格统一
- 居中卡片式表单，玻璃拟态效果
- 左侧/上方增加品牌展示区（Logo + 标语 + 装饰图形）
- 表单输入框聚焦态金色边框
- 按钮使用金色主按钮样式

#### 步骤 10：404 页面优化
- 电影感"胶片断裂"或"场记板"概念设计
- 深色背景，金色大数字"404"
- 返回首页按钮

### 阶段四：Drama 工作台与剧本页优化

#### 步骤 11：WorkspacePage 视觉优化
- 确认现有功能逻辑不变
- 页面背景改为深色沉浸模式
- 角色节点、进度条、状态指示使用金色作为活动/高亮色
- 按钮、卡片、Badge 统一使用新的 UI 组件
- 侧边/顶部导航样式与整体深色主题一致
- artifact 预览区深色背景适配

#### 步骤 12：ScriptsPage 视觉优化
- 剧本阅读区保持深色背景，降低视觉疲劳
- 质量评分、维度雷达图颜色与新品牌色对齐
- 问题列表、应用建议按钮等统一 UI 组件
- "修改建议" toast 提示样式与新 toast 主题一致

### 阶段五：Admin 后台对齐与后端清理

#### 步骤 13：Admin 页面样式对齐
- 检查所有 Admin 子页面的硬编码颜色类，将 indigo/blue 品牌色替换为 navy/gold
- 表格、筛选栏、分页组件样式统一
- drama-models 配置页确保与新设计系统一致
- 数据卡片、图表颜色适配深色主题

#### 步骤 14：后端文案清理
- defaults.py 文件头注释从"36个角色的默认定义"改为"12个专业角色的默认定义"
- 删除/更新任何残留的"36角色"相关注释（经搜索，业务逻辑已是12角色，无需改动）
- 确认 DRAMA_DEPARTMENTS 保持 8 部门（与现有 12 角色匹配）

### 阶段六：验证与打磨

#### 步骤 15：全链路验证
- 前端生产构建 (`npm run build`) 确保无编译错误
- 逐个页面检查视觉一致性
- 检查交互状态：hover/active/disabled/loading/error/empty
- 移动端响应式检查
- 后端 Python 语法检查
- 验证所有"36角色"文案已清理完毕
- 检查所有页面使用统一的 Button/Card/Badge 组件，无遗留 CSS 按钮类

## 潜在依赖与注意事项

1. **技术栈**：保持 React + Tailwind + framer-motion + sonner + lucide-react，不新增依赖
2. **向后兼容**：
   - 角色体系的"不向后兼容"仅指 UI 文案层面彻底删除 36 角色表述
   - 后端 DRAMA_ROLE_DEFAULTS 数据结构不变（历史数据中可能存在旧 agent_id 引用，保留数据库兼容性）
   - API 响应结构不变，仅前端视觉重构
3. **业务逻辑零改动**：所有服务、路由、状态管理、API 调用保持原样，只改表现层
4. **现有组件复用**：最大化复用已有的 Button/Card/Badge/Modal 等组件，仅升级样式
5. **图片资源**：Hero 背景图使用现有 text_to_image API 生成符合电影感的新图
6. **字体加载**：Noto Serif SC / Noto Sans SC 通过 Google Fonts CDN 加载（需确认项目已有字体加载机制）

## 风险处理

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 深色化改造导致部分页面可读性下降 | 中 | 严格控制文字对比度（正文≥4.5:1），重要信息用金色高亮 |
| Tailwind 色板修改影响范围大 | 高 | 保留原有色板名称（brand/accent）仅改色值，避免大面积类名替换 |
| 首页大改引入回归 bug | 中 | 保持所有链接、按钮、表单的功能逻辑不变，仅改样式和布局结构 |
| 字体加载影响首屏性能 | 低 | 使用 font-display: swap，预加载关键字体 |
| Admin 后台用户不习惯深色 | 低 | Admin 本来就是深色主题，本次是优化而非切换，用户无感知门槛 |
| 遗留 CSS 类删除导致样式丢失 | 中 | 全局搜索确认无页面使用后再删除，删除后全页面冒烟测试 |

## 实施顺序建议

按依赖关系严格顺序执行：
1. 设计令牌 (tailwind.config.js + globals.css) → 2. UI 基础组件 → 3. Layout → 4. 首页 → 5. Drama 入口页 → 6. 工作台/剧本页 → 7. 登录/404 → 8. Admin对齐 → 9. 后端文案 → 10. 全量验证

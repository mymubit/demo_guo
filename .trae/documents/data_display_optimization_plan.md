# 数据展示页面优化计划

## 一、调研结论

### 核心问题定位

经过全面代码调研，**最严重的问题**是核心数据展示组件 **DramaPresentation.jsx**（1700+ 行）完全使用浅色主题样式，与新的深色电影工业风设计系统严重脱节：

| 问题 | 位置 | 影响 |
|---|---|---|
| **核心展示组件全浅色** | `DramaPresentation.jsx` 所有子组件 | 工作台中角色执行输出全部是白底黑字，视觉割裂 |
| **色彩体系不统一** | MetricsBlock/HeroBlock/KvBlock 等使用 indigo-600 等旧品牌色 | 与新的暖金 #f4b719 主题冲突 |
| **卡片/边框/背景** | 大量使用 bg-white/border-gray-200/text-gray-900 | 在深色背景下刺眼、对比度错误 |
| **交互状态样式** | hover/focus/active 状态都是浅色设计 | 深色下无反馈或反馈不明显 |
| **剧本场次展示** | ScriptSceneBeat 场次/对白/动作样式 | 剧本阅读体验差 |
| **数据可视化弱** | 进度/评分/统计仅用简单数字 | 缺少专业感的可视化展示 |
| **信息层级不清晰** | 标题/正文/辅助信息颜色对比不足 | 信息扫读效率低 |

### 涉及文件优先级

**P0 最高优先级（核心体验）：**
1. `frontend/src/components/drama/presentation/DramaPresentation.jsx` - 全量深色化重写

**P1 高优先级（页面级优化）：**
2. `frontend/src/pages/Drama/WorkspacePage.jsx` - 欢迎面板/角色详情信息展示优化
3. `frontend/src/pages/Drama/ScriptsPage.jsx` - 剧本阅读器体验优化
4. `frontend/src/pages/Drama/index.jsx` - 项目卡片/创建表单优化

**P2 中优先级（Admin 后台）：**
5. `frontend/src/pages/Admin/drama-models/index.jsx` - 模型配置深色适配
6. `frontend/src/components/layout/AdminLayout.jsx` - 后台布局优化
7. 其他 Admin 页面深色化

---

## 二、DramaPresentation 组件深色化详细方案

### 色彩映射表

将组件中所有浅色 class 映射到深色主题：

| 旧样式 (浅色) | 新样式 (深色) | 用途 |
|---|---|---|
| `bg-white` | `bg-white/[0.04]` | 卡片背景 |
| `bg-gray-50` / `bg-slate-50` | `bg-white/[0.03]` | 次级背景 |
| `border-gray-100` / `border-gray-200` | `border-white/10` | 边框 |
| `text-gray-900` | `text-slate-100` | 主文字 |
| `text-gray-800` | `text-slate-200` | 正文文字 |
| `text-gray-700` | `text-slate-300` | 次要文字 |
| `text-gray-600` | `text-slate-400` | 辅助文字 |
| `text-gray-500` / `text-gray-400` | `text-slate-500` | 说明文字 |
| `bg-indigo-50` | `bg-gold-500/10` | 品牌色背景 |
| `bg-indigo-100` | `bg-gold-500/15` | 品牌色强调背景 |
| `text-indigo-600` / `text-indigo-700` | `text-gold-400` / `text-gold-300` | 品牌色文字 |
| `bg-emerald-50` | `bg-emerald-500/10` | 成功背景 |
| `text-emerald-600` / `text-emerald-700` | `text-emerald-400` | 成功文字 |
| `border-emerald-100` | `border-emerald-500/20` | 成功边框 |
| `bg-red-50` | `bg-red-500/10` | 危险/失败背景 |
| `text-red-600` | `text-red-400` | 危险文字 |
| `border-red-100` / `border-red-200` | `border-red-500/20` | 危险边框 |
| `bg-amber-50` | `bg-amber-500/10` | 警告背景 |
| `text-amber-700` / `text-amber-800` | `text-amber-300` | 警告文字 |
| `border-amber-100` / `border-amber-200` | `border-amber-500/20` | 警告边框 |
| `bg-violet-50` | `bg-cyan-500/10` | 信息/复合角色背景 |
| `text-violet-700` / `text-violet-800` | `text-cyan-300` | 信息文字 |
| `border-violet-100` | `border-cyan-500/20` | 信息边框 |
| `bg-sky-50` | `bg-sky-500/10` | 次要信息背景 |
| `text-sky-700` / `text-sky-800` | `text-sky-300` | 次要信息文字 |
| `border-sky-100` | `border-sky-500/20` | 次要信息边框 |
| `bg-rose-50` | `bg-rose-500/10` | 情绪/情感背景 |
| `text-rose-700` | `text-rose-300` | 情绪文字 |
| `shadow-sm` | `shadow-none` 或 `shadow-lg shadow-black/10` | 阴影调整 |
| `hover:bg-gray-50` | `hover:bg-white/[0.08]` | hover 状态 |

### 子组件深色化清单（按顺序）

1. **SectionTitle** - 标题竖线改为金色
2. **MetricsBlock** - 指标卡片玻璃态化，金色文字
3. **HeroBlock** - 核心创意区深色渐变背景
4. **KvBlock** - 键值对区块深色化
5. **ParagraphBlock** - 段落区块
6. **ListBlock** - 列表项圆点改为金色
7. **CalloutBlock** - 提示框深色变体
8. **StepsBlock** - 步骤时间轴深色化
9. **OutlineOverviewBlock** - 大纲概览（含节奏校验/反转点）
10. **EpisodeEmotionRow** - 情绪标签深色化
11. **EpisodeStructureTimeline** - 四段结构时间轴
12. **EpisodeOutlineCard** - 分集大纲卡片
13. **StageOutlinesBlock** - 阶段大纲折叠面板
14. **BriefProfileCard** - 简介卡片
15. **CharacterNode** - 角色节点头像
16. **RelationshipCard** - 人物关系卡片
17. **CardsBlock** - 卡片网格
18. **ReviewOverviewBlock** - 审稿结论
19. **ReviewIssuesBlock** - 审稿问题列表
20. **VerdictBlock** - 结论区块
21. **ComplianceReportBlock** - 合规报告
22. **QualityReportBlock** - 质量评分报告（含S/A/B等级金色渐变）
23. **ScoreBoardBlock** - 评分板
24. **ChecksBlock** - 检查项
25. **ScriptSceneBeat** - 剧本场次（场景头/动作/对白专业排版）
26. **ScriptEpisodesBlock** - 剧本分集折叠（含快速跳转）
27. **PlanOverviewBlock** - 计划概览
28. **PlanItemsBlock** - 计划项
29. **CharacterRosterBlock** - 角色档案
30. **RelationshipGraphBlock** - 人物关系网络
31. **MarketReportItem/Section** - 市场分析报告

---

## 三、页面级展示优化

### WorkspacePage 优化
- 欢迎面板统计卡片更具电影感（金色渐变数字）
- 角色详情面板信息分组更清晰
- 执行中状态动效优化
- 依赖/产物徽章视觉层次优化

### ScriptsPage 优化
- 剧本阅读器优化：更好的字体、行高、段落间距
- 场景头金色高亮
- 对白缩进+角色名青色高亮
- 质量评分面板：雷达图/进度条深色化
- 集数导航改进

### Drama/index 创作中心优化
- 项目卡片封面占位图（电影胶片风格）
- 创建项目模态框表单深色化
- 项目状态徽章优化

---

## 四、Admin 后台深色适配（基础）

- AdminLayout 侧边栏深色化
- 模型配置页面基础深色适配
- Dashboard 统计卡片深色化
- 表格/表单控件基础深色样式

---

## 五、实施步骤

### Phase 1: DramaPresentation 全量深色化（核心）
1. 系统性替换所有颜色 class 为深色主题映射
2. 优化剧本场次展示的专业排版（场景头/动作/对白区分）
3. 质量评分S/A/B等级使用金色/青色/橙色渐变徽章
4. 步骤时间轴连接线改为金色半透明
5. 情绪标签使用对应色系的深色半透明背景

### Phase 2: Workspace + Scripts 页面展示优化
1. WorkspacePage 欢迎面板视觉升级
2. ScriptsPage 阅读器体验优化
3. 角色详情面板信息架构优化

### Phase 3: 创作中心 + 首页展示优化
1. Drama/index 项目卡片优化
2. Home 页面特性卡片展示优化

### Phase 4: Admin 基础深色适配
1. AdminLayout 深色侧边栏
2. drama-models 页面深色化
3. 通用表格/表单深色样式

### Phase 5: 构建验证与细节打磨
1. 全量构建检查
2. 各页面视觉走查
3. 间距/对齐/对比度微调

---

## 六、风险与注意事项

1. **组件体量较大**：DramaPresentation 1700+行，改动时需保持功能不变，仅替换样式
2. **class 替换准确性**：使用全局查找替换 + 人工校验，避免漏换或错换
3. **保持语义**：成功/警告/危险/信息的语义色保持不变，仅调整明度/透明度
4. **向后兼容**：不改变组件props接口和数据结构，纯视觉改动
5. **剧本可读性**：剧本内容区域保持足够对比度，避免深色下阅读疲劳

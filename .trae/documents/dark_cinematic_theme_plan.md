# 深色电影主题更新实施计划

## 概述
将指定页面更新为 navy-950 底色 + gold 金色品牌色的深色电影主题，保持所有功能、props、逻辑、路由完全兼容。

---

## 1. 后端文件：`/workspace/backend/apps/drama/defaults.py`

### 修改内容
- **第 2 行 docstring**：将 `"Drama Skills 36个角色的默认定义。"` 改为 `"Drama Skills 12个角色的默认定义。"`
- 其他代码保持不变

---

## 2. 认证页面：AuthShell.jsx (`/workspace/frontend/src/pages/Auth/AuthShell.jsx`)

### 修改内容
| 元素 | 当前样式 | 新样式 |
|------|----------|--------|
| 容器 | `bg-gray-50` | `bg-navy-950` |
| 左侧面板 | `bg-brand-600` | `bg-navy-900` |
| 左侧渐变 | `from-brand-700/90 to-brand-900/95` | `from-gold-900/20 to-navy-950` |
| AUTH_BG 图片 | `opacity-30` | `opacity-20` |
| 描述文字 | `text-brand-100` | `text-slate-300` |
| 底部特性文字 | `text-brand-100` | `text-slate-400` |
| 右侧表单区域 | `bg-white p-8 md:p-12` | `bg-navy-900/50 backdrop-blur p-8 md:p-12` |
| tab 容器 | `border-gray-200 bg-gray-50` | `bg-white/5 border-white/10` |
| active tab | `bg-white text-gray-900 shadow-sm` | `bg-white/10 text-white` |
| inactive tab | `text-gray-500 hover:text-gray-900` | `text-slate-400 hover:text-white` |
| h1 标题 | `text-gray-900` | `text-white` |
| subtitle | `text-gray-500` | `text-slate-400` |

---

## 3. 登录页面：Login.jsx (`/workspace/frontend/src/pages/Auth/Login.jsx`)

### 修改内容
| 元素 | 当前样式 | 新样式 |
|------|----------|--------|
| 密码 label | `text-gray-600` | `text-slate-300` |
| "忘记密码？"链接 | `text-brand-600 hover:text-gold-300` | `text-gold-400 hover:text-gold-300` |
| 密码显示按钮 | `text-gray-400 hover:text-brand-600` | `text-slate-400 hover:text-gold-400` |
| 底部文字 | `text-gray-500` | `text-slate-400` |
| 底部 link | `text-brand-600` | `text-gold-400` |

### 注意事项
- 登录按钮已经使用 `variant="gold"`，保持不变
- Input 组件会跟随深色主题自动适配

---

## 4. 注册页面：Register.jsx (`/workspace/frontend/src/pages/Auth/Register.jsx`)

### 修改内容
| 元素 | 当前样式 | 新样式 |
|------|----------|--------|
| 所有 label | `text-gray-600` | `text-slate-300` |
| label 说明文字 | `text-gray-400` | `text-slate-500` |
| icon 颜色 | `text-gray-400` | `text-slate-500` |
| 密码显示按钮 | `text-gray-400 hover:text-brand-600` | `text-slate-400 hover:text-gold-400` |
| 密码强度条背景 | `bg-gray-100` | `bg-white/10` |
| 成功文字 | `text-green-400` | 保持 `text-green-400`（已正确） |
| 底部文字 | `text-gray-500` | `text-slate-400` |
| 底部 link | `text-brand-600` | `text-gold-400` |
| 同意条款文字 | `text-gray-500` | `text-slate-500` |
| 同意条款 link | `text-brand-600` | `text-gold-400` |
| 注册按钮 | 内联样式渐变按钮 | 使用 Button 组件 `variant="gold"` |
| AlertCircle icon | `text-brand-600` | `text-gold-400` |

### 注意事项
- `.sf-control` 类已在 globals.css 中定义为深色样式（border-white/10 bg-white/5 等），无需重复添加

---

## 5. 404 页面：NotFound.jsx (`/workspace/frontend/src/pages/NotFound.jsx`)

### 修改内容
| 元素 | 当前样式 | 新样式 |
|------|----------|--------|
| 容器背景 | `bg-gray-50` | `bg-navy-950` |
| 路由修复 | SUGGESTION_ICONS 和 SUGGESTIONS 中 `/creation` | 改为 `/drama` |
| icon 容器 | `border-gray-200 bg-gray-50` | `border-white/10 bg-white/5` |
| Compass icon | `text-brand-600` | `text-gold-400` |
| h1 404 | `text-gray-900` | 使用金色渐变（bg-clip-text） |
| h2 | `text-gray-900` | `text-white` |
| 描述文字 | `text-gray-500` | `text-slate-400` |
| 返回首页按钮 | `btn-gold` | Button 组件 `variant="gold"` |
| 上一页按钮 | `btn-ghost` | Button 组件 `variant="secondary"` |
| 建议区域 card | `border-gray-200 bg-white` | `border-white/10 bg-white/[0.04] backdrop-blur-sm` |
| 建议区域 h3 | `text-gray-900` | `text-white` |
| Search icon | `text-brand-600` | `text-gold-400` |
| 建议链接 | `border-gray-200 bg-gray-50 hover:border-brand-200 hover:bg-brand-50` | `border-white/10 bg-white/5 hover:border-gold-500/30 hover:bg-gold-500/10` |
| 建议 link icon | `text-gray-500 group-hover:text-brand-600` | `text-slate-500 group-hover:text-gold-400` |
| 建议 link 文字 | `text-gray-600 group-hover:text-gray-900` | `text-slate-400 group-hover:text-white` |
| 底部提示 | `text-gray-400` | `text-slate-500` |

### 额外修改
- 需要导入 Button 组件
- 将 `<Link>` 按钮改为使用 Button 组件包裹

---

## 6. Drama 首页：index.jsx (`/workspace/frontend/src/pages/Drama/index.jsx`)

### 修改内容
| 区域 | 元素 | 当前样式 | 新样式 |
|------|------|----------|--------|
| 页面容器 | 背景 | `bg-slate-25` | `bg-navy-950` |
| 顶栏 | 容器 | `bg-white border-b border-slate-200` | `bg-navy-900/80 backdrop-blur-xl border-b border-white/10` |
| | h1 标题 | `text-slate-900` | `text-white` |
| | subtitle | `text-slate-500` | `text-slate-400` |
| | 新建按钮 | `variant="brand"` | `variant="gold"` |
| 快速通道卡片 | Card | `border-brand-100 bg-gradient-to-br from-brand-50/50 to-white` | `border-gold-500/20 bg-gradient-to-br from-gold-500/10 to-navy-900/50` |
| | icon 容器 | `bg-brand-100` | `bg-gold-500/20` |
| | Zap icon | `text-brand-600` | `text-gold-400` |
| | h3 | `text-slate-900` | `text-white` |
| | 描述 | `text-slate-500` | `text-slate-400` |
| | Badge | `tone="brand"` | `tone="gold"` |
| 专家通道卡片 | Card | `border-accent-100 bg-gradient-to-br from-accent-50/50 to-white` | `border-slate-500/20 bg-gradient-to-br from-slate-800/30 to-navy-900/50` |
| | icon 容器 | `bg-accent-100` | `bg-slate-700/50` |
| | Film icon | `text-accent-600` | `text-slate-300` |
| | h3 | `text-slate-900` | `text-white` |
| | 描述 | `text-slate-500` | `text-slate-400` |
| | Badge | `tone="accent"` | `tone="default"`（或保持灰色） |
| "我的项目" | 标题 | `text-slate-800` | `text-white` |
| | count | `text-slate-400` | `text-slate-500` |
| EmptyState | - | - | 检查 EmptyState 组件是否有深色适配，若不适用则用内联样式覆盖（但优先保持组件使用） |
| 新建项目按钮 | - | `variant="brand"` | `variant="gold"` |
| Modal 弹窗 | - | - | 检查 Modal 组件深色样式 |
| Modal label | | `text-slate-700` | `text-slate-300` |
| Modal input/select/textarea | | `border-slate-200 bg-white focus:ring-brand-500 focus:border-brand-500` | `border-white/10 bg-white/5 text-white placeholder:text-slate-500 focus:border-gold-500 focus:ring-gold-500/20` |
| Tab 切换容器 | | `bg-slate-100` | `bg-white/5` |
| active tab | | `bg-white text-brand-700` | `bg-gold-500/20 text-gold-300` |
| inactive tab | | `text-slate-500 hover:text-slate-700` | `text-slate-400 hover:text-white` |
| 推荐组合区域 | | `bg-brand-50/80 border-brand-100` | `bg-gold-500/10 border-gold-500/20` |
| 推荐组合标题 | | `text-brand-700` | `text-gold-400` |
| 推荐组合按钮（active） | | `bg-brand-600 text-white border-brand-600` | `bg-gold-500 text-navy-950 border-gold-500` |
| 推荐组合按钮（inactive） | | `bg-white text-slate-700 border-slate-200 hover:border-brand-400 hover:text-brand-700` | `bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300` |
| 维度标签 | | `text-slate-600` | `text-slate-400` |
| 维度 hint | | `text-slate-400` | `text-slate-500` |
| 维度按钮（selected） | | `bg-brand-600 text-white border-brand-600` | `bg-gold-500 text-navy-950 border-gold-500` |
| 维度按钮（unselected） | | `bg-white text-slate-700 border-slate-100 hover:border-brand-300 hover:text-brand-700` | `bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300` |
| 选中描述文字 | | `text-brand-100` | `text-gold-200` |
| 组合预览区域 | | `bg-slate-50 border-slate-100 text-slate-600` | `bg-white/5 border-white/10 text-slate-400` |
| 组合预览值 | | `text-brand-700` | `text-gold-400` |
| 预设模式卡片（active） | | `bg-brand-50 border-brand-400 ring-brand-400` | `bg-gold-500/10 border-gold-500/30 ring-gold-500/30` |
| 预设模式卡片（inactive） | | `border-slate-200 hover:border-brand-300 hover:bg-brand-50/30` | `border-white/10 hover:border-gold-500/30 hover:bg-gold-500/5` |
| 预设卡片标题 | | `text-slate-800` | `text-white` |
| 预设卡片热度 | | `text-slate-400` | `text-slate-500` |
| 自由输入提示文字 | | `text-slate-400` | `text-slate-500` |
| label 必填星号 | | `text-danger` | 保持 `text-danger` |
| 创建按钮 | | `variant="brand"` | `variant="gold"` |

### ProjectCard 组件修改
| 元素 | 当前样式 | 新样式 |
|------|----------|--------|
| Card | `hover:border-brand-300` | `variant="glass" hover:border-gold-500/30` |
| h3 标题 | `text-slate-900` | `text-white` |
| 描述 | `text-slate-400` | `text-slate-400`（保持） |
| 完成度 label | `text-slate-500` | `text-slate-400` |
| 完成度百分比 | `text-slate-700` | `text-slate-300` |
| 进度条背景 | `bg-slate-100` | `bg-white/10` |
| 进度条填充 | `from-brand-500 to-brand-600` | `from-gold-500 to-gold-400` |
| 评分 badge | `tone="accent"` | 根据分数调整为 gold 色系 |

---

## 7. 全局样式检查
- `globals.css` 中 `.sf-control` 已经是深色样式，无需修改
- Tailwind 配置中已有 navy-950、gold 等颜色，无需添加
- 检查 Button 组件是否有 variant="gold" 和 variant="secondary"（Login 中已使用 variant="gold"，说明存在）

---

## 执行顺序
1. 修改后端 defaults.py（最简单）
2. 修改 AuthShell.jsx
3. 修改 Login.jsx
4. 修改 Register.jsx
5. 修改 NotFound.jsx（含路由修复）
6. 修改 Drama/index.jsx（最复杂）
7. 运行 lint/typecheck 确保无错误

---

## 兼容性保证
- 所有 props、组件接口保持不变
- 所有路由保持不变（除了修复 NotFound 中过时的 `/creation` → `/drama`）
- 所有业务逻辑、表单验证、API 调用完全不变
- 只修改 Tailwind className 样式类

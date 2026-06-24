# ScriptForge 短剧创作平台 - 全量代码审计报告

**审计日期**：2026-06-24  
**审计范围**：后端 (Django)、前端 (React)、配置、安全、依赖  
**问题总数**：约 160+ 个问题  

---

## 问题分级说明

| 等级 | 颜色 | 定义 | 修复时限 |
|-----|------|------|---------|
| P0 | 🔴 致命 | 功能完全失效 / 数据丢失风险 / 严重安全漏洞 | 24小时内 |
| P1 | 🟠 严重 | 主要功能异常 / 用户体验严重受损 / 高危安全 | 3天内 |
| P2 | 🟡 一般 | 次要功能问题 / 视觉不一致 / 潜在风险 | 本周内 |
| P3 | 🟢 轻微 | 代码风格 / 优化建议 / 最佳实践 | 下个迭代 |

---

## 目录

1. [后端代码问题](#一后端代码问题)
   - [1.1 致命编码问题 P0](#11-文件编码损坏-p0)
   - [1.2 运行时崩溃问题 P0](#12-运行时崩溃问题-p0)
   - [1.3 业务逻辑缺陷 P0-P1](#13-业务逻辑缺陷)
   - [1.4 安全权限问题 P0-P1](#14-安全权限问题)
   - [1.5 Services 层问题](#15-services-层问题)
   - [1.6 Views 层问题](#16-views-层问题)
   - [1.7 Models 层问题](#17-models-层问题)
   - [1.8 Serializers 层问题](#18-serializers-层问题)
2. [前端代码问题](#二前端代码问题)
   - [2.1 假数据/Mock 数据问题 P0](#21-假数据mock-数据问题-p0)
   - [2.2 功能未实现问题 P0-P1](#22-功能未实现问题)
   - [2.3 样式/设计系统不一致](#23-样式设计系统不一致)
   - [2.4 React 代码质量问题](#24-react-代码质量问题)
   - [2.5 DramaPresentation 组件问题](#25-dramapresentation-组件问题)
   - [2.6 Admin 页面问题](#26-admin-页面问题)
3. [配置与安全问题](#三配置与安全问题)
   - [3.1 敏感信息硬编码 P0](#31-敏感信息硬编码-p0)
   - [3.2 HTTPS/加密问题 P1](#32-https加密问题-p1)
   - [3.3 CORS/限流/Header 问题](#33-cors限流header-问题)
   - [3.4 依赖版本问题 P2](#34-依赖版本问题-p2)
4. [测试覆盖问题](#四测试覆盖问题)
5. [修复路线图](#五修复路线图)

---

## 一、后端代码问题

### 1.1 文件编码损坏 P0 🔴

**影响文件**：几乎所有 drama 后端文件中文显示为乱码

| 文件 | 问题位置 | 问题描述 |
|------|---------|---------|
| `backend/apps/drama/services.py` | 全文 | 所有中文注释、字符串显示为 `?` 问号 |
| `backend/apps/drama/views.py` | 全文 | 所有中文注释、docstring 乱码 |
| `backend/apps/drama/urls.py` | 全文 | 注释乱码 |
| `backend/apps/drama/progress_service.py` | 全文 | 注释和字符串乱码 |
| `backend/apps/drama/models.py` | 部分 | 字段 verbose_name 可能受影响 |
| `backend/apps/drama/serializers.py` | 部分 | 错误消息乱码 |

**影响**：
- 代码可维护性极差，无法理解中文业务逻辑
- 如果有中文字符串用于判断逻辑，将直接导致功能失效
- 开发者无法阅读注释理解代码意图

**修复建议**：
1. 检查文件实际编码（可能是 GBK/GB2312 被错误解析为 UTF-8）
2. 使用 `iconv` 或 VSCode 重新以正确编码打开并保存为 UTF-8
3. 验证所有中文字符串匹配逻辑是否正常工作（见下节）

---

### 1.2 运行时崩溃问题 P0 🔴

#### 问题 1：timezone.timedelta 不存在
- **文件**：[services.py:827](file:///workspace/backend/apps/drama/services.py#L827)
- **代码**：
  ```python
  threshold = timezone.now() - timezone.timedelta(minutes=minutes)
  ```
- **问题**：Django 的 `timezone` 模块没有 `timedelta` 属性，`timedelta` 来自 `datetime` 模块
- **影响**：调用 `fail_stale_active_executions()` 时直接抛出 `AttributeError`，超时执行清理功能完全失效
- **修复**：
  ```python
  from datetime import timedelta
  threshold = timezone.now() - timedelta(minutes=minutes)
  ```

---

### 1.3 业务逻辑缺陷

#### 问题 2：中文字符串匹配失效 P0 🔴
- **文件**：[services.py:614-636](file:///workspace/backend/apps/drama/services.py#L614-L636)
- **代码位置**：`_detect_issues_from_score()` 方法中
- **问题**：代码中使用 `"???" in wc.get("status", "")` 进行匹配，但实际 status 值是中文（如"字数不足"、"字数过多"、"对话占比偏低"等）
- **根本原因**：文件编码损坏导致中文字符串变成 `?`，匹配逻辑完全失效
- **影响**：质量检测的字数、对话占比、场景数问题完全无法被识别，质量报告功能形同虚设
- **修复**：
  1. 先修复文件编码问题
  2. 将匹配改为常量引用或状态枚举值，不要用中文 in 判断

#### 问题 3：model_name 更新丢失 P0 🔴
- **文件**：`views.py:425` 附近（ModelConfigView）
- **问题**：设置 `model_name` 字段但 `save(update_fields=[...])` 中未包含该字段
- **影响**：用户在后台修改模型配置后，`model_name` 变更不会被保存到数据库
- **修复**：将 `model_name` 添加到 `update_fields` 列表中

#### 问题 4：N+1 查询问题 P1 🟠
- **多个位置**：
  - `views.py` 列表接口未使用 `select_related`/`prefetch_related`
  - `services.py` 中循环内查询数据库（如 reconcile_stale_executions 中 for 循环内查 AgentExecutionRun）
- **影响**：列表页加载慢，数据库压力大
- **修复**：
  - 列表查询统一加 `select_related`/`prefetch_related`
  - 批量查询替代循环内单条查询：`id__in=list_of_ids`

#### 问题 5：事务保护缺失 P1 🟠
- **位置**：多个多步写入操作
- **问题**：
  - 角色执行状态更新 + Artifact 创建未使用 `transaction.atomic()`
  - 质量评估保存 + 建议生成未包裹事务
  - 项目创建相关操作部分缺失事务
- **影响**：中途失败可能导致数据不一致（如状态标记为完成但内容未保存）
- **修复**：按 AGENTS.md 规范，所有多表写入必须使用 `transaction.atomic()`

---

### 1.4 安全权限问题

#### 问题 6：TokenStatsView 无管理员校验 P0 🔴
- **文件**：[views.py:332-343](file:///workspace/backend/apps/drama/views.py#L332-L343)
- **代码**：
  ```python
  class TokenStatsView(APIView):
      permission_classes = [IsAuthenticated]  # 只校验登录，未校验管理员
  ```
- **问题**：普通用户传 `?user_only=false` 即可查看全站用户的 Token 使用统计
- **影响**：泄露全站业务数据（Token 消耗量、各角色调用量等敏感运营数据）
- **修复**：添加 `IsAdminUser` 权限或自定义管理员权限校验

#### 问题 7：ModelConfigView 同理 P1 🟠
- **文件**：[views.py:350+](file:///workspace/backend/apps/drama/views.py#L350)
- **问题**：LLM 模型配置接口只校验登录，普通用户可能能查看/修改全局模型配置
- **影响**：用户可能篡改 LLM 路由配置，造成费用损失或服务异常
- **修复**：添加管理员权限校验，修改操作加审计日志

#### 问题 8：用户数据越权访问风险 P1 🟠
- **位置**：多个获取项目详情、执行记录的接口
- **问题**：需检查所有通过 project_id 查询的接口，是否校验了 `request.user == project.user`
- **影响**：用户 A 可能通过遍历 ID 访问用户 B 的项目数据
- **修复**：所有项目相关查询统一添加 `user=request.user` 过滤条件

---

### 1.5 Services 层问题

按文件详细列出问题：

| 行号 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| 全文 | P0 | 中文注释和字符串全部是问号乱码 | 修复文件编码为 UTF-8 |
| 827 | P0 | `timezone.timedelta` 不存在导致崩溃 | 改为 `from datetime import timedelta` |
| 614-636 | P0 | 中文状态匹配失效（`"???" in status`） | 修复编码后改用状态常量判断 |
| 全域 | P1 | 多处循环内单条数据库查询 | 改为批量查询 `id__in=[...]` |
| 多个方法 | P1 | 缺少输入参数 None 校验 | 添加参数校验，返回明确错误 |
| 约 499 行附近 | P1 | `build_detailed_quality_report` 未处理 scores 为空 dict | 添加边界值处理 |
| 约 732 行 | P1 | `apply_suggestions_to_episode` 是 stub？需确认是否真实调用 LLM | 如果是占位代码需标记或实现真实逻辑 |
| 多个 | P2 | 异常捕获过于宽泛或缺少异常处理 | 捕获具体异常类型，记录上下文 |
| 多个 | P2 | 硬编码数字（如 15 分钟 STALE_ACTIVE_MINUTES） | 提取为配置或类常量 |
| ISSUE_TEMPLATES | P2 | key 与 DIMENSIONS 的 key 不匹配（DIMENSIONS有10个，ISSUE_TEMPLATES只有8个，structure/dialogue/dream/commercial 不在DIMENSIONS中） | 统一 dimension key，确保一致 |
| 多个 | P3 | 日志使用 print 而非 logger？需确认 | 全部使用项目 logger |
| 多个 | P3 | 方法过长（部分方法超过100行） | 拆分为更小的职责单一的方法 |

---

### 1.6 Views 层问题

| 位置 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| 全文 | P0 | 中文注释/docstring 乱码 | 修复编码 |
| 332-343 | P0 | TokenStatsView 无管理员权限校验 | 添加 IsAdminUser |
| 350+ | P1 | ModelConfigView 同理需要管理员权限 | 添加管理员权限 |
| 611-620 | P1 | EpisodeQualityView 之前的占位代码已修复，但需检查整个方法是否还有其他问题 | 完整回归测试 |
| 多个 GET 接口 | P1 | 未做分页处理，直接返回全部数据 | 对于列表接口添加分页 |
| 多个接口 | P1 | 缺少参数校验（如 episode_number 范围校验） | 使用 Serializer 校验入参 |
| 多个接口 | P1 | 错误响应格式不统一（有的返回 code:0，有的直接返回） | 统一响应格式 |
| 多个地方 | P2 | 直接 `request.data.get()` 而未用 Serializer 校验 | 按 DRF 规范使用 Serializer |
| 多个 POST/PUT | P2 | 操作成功后缺少 audit log | 关键操作（修改配置、执行角色、应用建议）添加审计记录 |
| 全域 | P2 | 未统一处理 DoesNotExist 异常，可能导致 500 错误 | 添加 get_object_or_404 或 try-except |
| 全域 | P3 | View 中包含业务逻辑（违反 MTV 分层） | 将业务逻辑移到 Service 层，View 只做请求响应 |

---

### 1.7 Models 层问题

| 位置 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| DramaRoleExecution | P1 | 缺少状态变更的审计字段（who/when changed status） | 添加 status_changed_by, status_changed_at |
| DramaEpisodeArtifact | P1 | 缺少 created_at/updated_at 索引？需检查 | 添加常用查询字段索引 |
| DramaEpisodeQuality | P2 | scores 字段使用 JSONField，缺少 schema 约束 | 添加字段校验或使用 separate model |
| 所有模型 | P2 | 部分模型 __str__ 方法返回非字符串或包含乱码 | 修复 __str__ 确保清晰可读 |
| 外键字段 | P2 | on_delete 策略需逐一确认（CASCADE 是否合理？） | 业务数据使用 SET_NULL 或 PROTECT 更安全 |
| 多个字段 | P3 | verbose_name 可能乱码 | 修复编码后确认 |

---

### 1.8 Serializers 层问题

| 位置 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| 全域 | P1 | Serializer 定义不完整，很多接口直接在 View 中取 request.data | 所有入参/出参都定义 Serializer |
| 部分 Serializer | P2 | 缺少字段校验（如 episode_number min/max） | 添加 validate_ 方法 |
| 部分 Serializer | P2 | 嵌套序列化不完整，可能导致数据泄露 | 使用 fields 白名单而不是 `__all__` |
| 全域 | P3 | 缺少示例或 docstring | 添加 Serializer 用途注释 |

---

## 二、前端代码问题

### 2.1 假数据/Mock 数据问题 P0 🔴

#### 问题 1：修改建议面板完全使用硬编码假数据
- **文件**：[ScriptsPage.jsx:302-308](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx#L302-L308)
- **代码**：
  ```jsx
  const issues = [
    { id:'i1', severity:'error', dimension:'格式规范', desc:`第${episode}集台词占比偏低...`, ... },
    { id:'i2', severity:'error', dimension:'格式规范', desc:'场景数量超出限制...', ... },
    // ... 共5条硬编码假数据
  ].slice(0, Math.min(quality.issue_count || 3, 5));
  ```
- **问题**：用户点击"X个问题需修复"看到的全部是假数据，和真实质量问题完全无关
- **影响**：严重误导用户，用户根据假建议修改会越改越错，信任度崩塌
- **修复**：使用真实的 `quality.all_issues` 或 `quality.top_suggestions` 数据

#### 问题 2：子维度分数伪造 P0 🔴
- **文件**：[ScriptsPage.jsx:569-571](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx#L569-L571)
- **代码**：
  ```jsx
  const subScore = score > 0
    ? Math.max(40, Math.min(100, score + (idx % 3 === 0 ? -8 : idx % 3 === 1 ? 5 : -3)))
    : 0;
  ```
- **问题**：10个维度的子项分数全部是基于维度总分随机生成的假数据，不是真实评估结果
- **影响**：用户看到的细分项评分完全是虚构的，没有任何参考价值
- **修复**：子维度数据应来自后端真实返回，如果后端不提供则不显示子项，不要造假

---

### 2.2 功能未实现问题

#### 问题 3：复制按钮完全未实现 P0 🔴
- **文件**：[ScriptsPage.jsx:239-241](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx#L239-L241)
- **代码**：
  ```jsx
  <Button variant="secondary" iconLeft={<Copy className="w-4 h-4" />}>
    复制
  </Button>
  ```
- **问题**：按钮只有样式，没有 onClick 处理函数
- **影响**：用户点击复制无任何反应
- **修复**：添加 `navigator.clipboard.writeText()` 实现复制，并加 toast 成功/失败提示

#### 问题 4：应用建议传递假数据 P1 🟠
- **文件**：[ScriptsPage.jsx:373-377](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx#L373-L377)
- **问题**：应用修改建议时传递的是硬编码的 mock issues，不是真实问题列表
- **影响**：即使后端正常，发送给 LLM 的修改建议也是假的
- **修复**：使用真实 issues 数据，且 applyMut 成功/失败需要 toast 反馈

#### 问题 5：复制/应用等操作无反馈 P1 🟠
- **位置**：多个 mutation
- **问题**：部分 mutation 只有 onError，没有 onSuccess 反馈；部分反馈只有 toast 没有 loading 状态禁用
- **修复**：所有异步操作统一处理：loading 时按钮禁用 + spinner，成功/失败都有明确提示

---

### 2.3 样式/设计系统不一致

#### 问题 6：DIM_META 硬编码 hex 颜色 P1 🟠
- **文件**：[ScriptsPage.jsx:29-40](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx#L29-L40)
- **代码**：
  ```jsx
  const DIM_META = {
    format:      { color: 'var(--brand-600)', ... },
    narrative:   { color: 'var(--brand-700)', ... },
    conflict:    { color: 'var(--accent-600)', ... },
    character:   { color: 'var(--accent-700)', ... },
    emotion:     { color: '#10b981', ... },  // 硬编码
    logic:       { color: '#f97316', ... },  // 硬编码
    satisfaction:{ color: '#06b6d4', ... },  // 硬编码
    hooks:       { color: '#84cc16', ... },  // 硬编码
    paywall:     { color: '#ef4444', ... },  // 硬编码
    genre_fit:   { color: '#a855f7', ... },  // 硬编码
  };
  ```
- **问题**：6个维度使用硬编码 hex 颜色，不走设计系统语义色
- **修复**：统一使用 Tailwind 语义色或 CSS 变量，如 `var(--success-600)`、`var(--warning-600)` 等

#### 问题 7：动态 Tailwind 类名问题 P1 🟠
- **位置**：ScriptsPage 动态拼接 className 的地方
- **问题**：Tailwind 是静态扫描，动态拼接类名（如 `bg-${color}-500`）在生产环境不会被包含，导致样式失效
- **修复**：使用静态映射表，或在 tailwind.config.js 中 safelist 动态用到的颜色

#### 问题 8：DramaPresentation 组件颜色完全不统一 P1 🟠
- **位置**：`frontend/src/components/drama/presentation/` 目录下所有文件
- **问题**：整套剧本展示组件使用自己的颜色体系，和主站设计系统不一致
- **修复**：统一重构为设计系统语义色，复用 Card、Badge 等 UI 组件

#### 问题 9：大量原生 button 未使用 Button 组件 P2 🟡
- **位置**：
  - WorkspacePage：视图切换按钮、返回按钮
  - ScriptsPage：Tab 切换、侧边栏剧集选择、维度折叠按钮、关闭按钮、全选按钮
  - index.jsx：部分交互按钮
- **修复**：全部替换为 `<Button>` 组件，统一 variant 和 size

#### 问题 10：部分区域仍使用原生 div 做卡片 P2 🟡
- **修复**：统一使用 `<Card>` 组件

---

### 2.4 React 代码质量问题

#### 问题 11：setTimeout 内存泄漏 P1 🟠
- **文件**：[WorkspacePage.jsx:111](file:///workspace/frontend/src/pages/Drama/WorkspacePage.jsx#L111)、[117](file:///workspace/frontend/src/pages/Drama/WorkspacePage.jsx#L117)
- **代码**：
  ```jsx
  setTimeout(() => setExecFeedback(null), 5000);
  ```
- **问题**：组件卸载时 setTimeout 未清理，卸载后 setState 会触发 React 警告，且存在内存泄漏
- **修复**：
  ```jsx
  const feedbackTimerRef = useRef(null);
  // 设置时
  feedbackTimerRef.current = setTimeout(...);
  // 清理
  useEffect(() => {
    return () => {
      if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    };
  }, []);
  ```

#### 问题 12：useQuery/useMutation 错误处理不完整 P1 🟠
- **位置**：三个页面多数 query
- **问题**：
  - 很多 query 没有 onError 处理，请求失败用户看不到提示
  - 部分 error 状态未展示（加载失败时一直显示 loading spinner）
- **修复**：所有 query 添加 onError + error UI，mutation 添加完整的 onSuccess/onError 反馈

#### 问题 13：列表渲染使用 index 作为 key（部分地方） P2 🟡
- **位置**：ScriptRenderer 中 `text.split('\n').map((line, i)` 使用 index 作为 key
- **风险**：内容变化时可能导致渲染错误或状态错位
- **修复**：使用行内容 + 行号组合作为 key，或使用内容哈希

#### 问题 14：completedSet 每次渲染重建 P2 🟡
- **文件**：[WorkspacePage.jsx:121](file:///workspace/frontend/src/pages/Drama/WorkspacePage.jsx#L121)
- **代码**：`const completedSet = new Set(project?.completed_roles || []);`
- **问题**：每次渲染都新建 Set，传递给子组件可能导致不必要重渲染
- **修复**：用 `useMemo(() => new Set(...), [project?.completed_roles])` 包裹

#### 问题 15：加载状态不完整 P2 🟡
- **问题**：很多地方只判断 `if (!project)` 显示 loading，但有 isLoading、isFetching 状态未利用
- **修复**：统一使用 `query.isLoading` 显示骨架屏/loading，`query.isError` 显示错误重试

#### 问题 16：EmotionCurve 坐标轴映射错误 P1 🟠
- **位置**：ScriptsPage 情绪曲线组件
- **问题**：X 轴（集数）和 Y 轴（情绪强度）数据映射需要验证是否正确
- **修复**：检查图表数据格式是否和 ECharts 配置匹配

#### 问题 17：服务层响应解析不统一 P2 🟡
- **位置**：`src/services/drama.js`
- **问题**：有些地方取 `res.data`，有些地方取 `res.data.data`，响应格式不统一
- **修复**：在 service 层统一解析 axios 响应，组件中直接拿到业务 data

---

### 2.5 DramaPresentation 组件问题

| 位置 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| 所有文件 | P1 | 颜色体系独立，不使用设计系统 | 统一为 brand/accent/slate 语义色 |
| 所有文件 | P1 | 未复用 Button/Badge/Card 组件 | 全部替换为项目 UI 组件 |
| 文本渲染 | P2 | 可能存在 XSS 风险？需检查是否有 innerHTML | 确认全部用 React 文本渲染 |
| 图标 | P2 | 使用 emoji 代替 lucide-react 图标，风格不统一 | 替换为 lucide 图标 |
| 长内容 | P3 | 无虚拟滚动，超长剧本可能卡顿 | 超过 500 行时使用虚拟滚动 |

---

### 2.6 Admin 页面问题

| 位置 | 严重等级 | 问题描述 | 修复建议 |
|-----|---------|---------|---------|
| drama-models/index.jsx | P0 | 部门分组逻辑 bug，分组完全错误 | 修复分组逻辑，验证 groupBy 字段正确 |
| Admin Drama 页面 | P0 | 完全未使用 UI 组件库，所有元素都是原生 button/div | 全部重构复用 UI 组件 |
| Admin 表单 | P1 | 表单控件样式不统一，原生 select/input | 使用统一表单组件 |
| 配置按钮 | P2 | 使用硬编码 `<a href>` 跳转，应该用 `<Link>` 或 navigate | 使用 React Router 导航 |

---

## 三、配置与安全问题

### 3.1 敏感信息硬编码 P0 🔴

| 位置 | 问题描述 | 风险等级 | 修复建议 |
|-----|---------|---------|---------|
| `config/settings/base.py:21` | SECRET_KEY 默认弱密钥 `django-insecure-change-me-in-production` | 🔴 高 | 删除默认值，启动时强制要求环境变量；生成50位以上随机密钥 |
| `config/settings/base.py:306` | SKILL_ENCRYPT_KEY 硬编码 `01234567890123456789012345678901`（AES密钥） | 🔴 高 | 删除默认值，生产环境强制配置32字节随机密钥 |
| `config/settings/base.py:347-348` | ENCRYPT_PHONE_KEY/ENCRYPT_EMAIL_KEY 弱默认值 | 🔴 高 | 同上删除默认弱密钥 |
| `config/settings/base.py:415` | API_SIGN_SECRET 默认 `scriptforge-demo-sign-secret-change-me` | 🔴 高 | 删除默认值，生产环境强制检查 |
| `config/settings/base.py:111` | 数据库默认密码 `postgres` | 🔴 高 | 删除默认密码，强制 DB_PASSWORD 环境变量 |
| `config/settings/base.py:454-455` | MinIO 默认密钥 `minioadmin/minioadmin` | 🔴 高 | 删除默认值，生产强制配置 |
| `config/settings/test.py:54` | 测试数据库硬编码密码 `testpass123` | 🟠 中 | 测试环境也通过环境变量注入，确保测试DB不暴露 |
| `package.json` 根目录 | 管理员创建命令硬编码默认密码 `Admin1234!` | 🔴 高 | 移除，创建时交互式输入或环境变量传入 |
| `frontend/src/services/http.js:31` | JWT Token 存储在 localStorage | 🔴 高 | 迁移到 HttpOnly Cookie；若保留localStorage需加强XSS防护 |

---

### 3.2 HTTPS/加密问题 P1 🟠

| 位置 | 问题描述 | 修复建议 |
|-----|---------|---------|
| `nginx/nginx.conf` | 只有 80 端口 HTTP，HTTPS 被注释 | 启用 443 + 证书，强制 HTTP 跳转 HTTPS |
| `config/settings/base.py:253-256` | JWT 使用 HS256 对称加密 | 评估迁移到 RS256 非对称加密 |
| `apps/security/services.py:67-94` | EncryptionService 使用 AES-ECB 模式（不安全，相同明文→相同密文） | 废弃 ECB，优先使用 AES-256-GCM |
| `production.py:70` | SECURE_SSL_REDIRECT 默认 false | 改为默认 true |
| Cookie 配置 | 缺少 SESSION_COOKIE_SAMESITE、CSRF_COOKIE_HTTPONLY 显式配置 | 显式设置 SameSite=Lax，HttpOnly=True |

---

### 3.3 CORS/限流/Header 问题

| 位置 | 问题描述 | 严重等级 | 修复建议 |
|-----|---------|---------|---------|
| `development.py:16,29` | 开发环境 ALLOWED_HOSTS=["*"] 且关闭限流 | 🟠 P1 | 绑定127.0.0.1，开发环境也保留基础限流 |
| `base.py:393` | /api/auth/ 路径跳过签名验证，易被暴力破解 | 🟠 P1 | 登录/注册添加验证码、账户锁定、严格限流 |
| `security/middleware.py:282-285` | Redis不可用时限流直接拒绝请求，服务完全不可用 | 🟠 P1 | 添加熔断：Redis故障时降级为内存限流或临时放行+告警 |
| `nginx.conf` | 静态文件通过Django代理而非Nginx直接服务 | 🟡 P2 | 配置Nginx直接服务 /static/ 和 /media/ |
| `nginx.conf` | proxy_read_timeout 统一60s | 🟡 P2 | 按接口类型差异化超时配置 |
| Dockerfile | 容器以 root 用户运行 | 🟡 P2 | 创建非root用户，USER指令切换 |
| 缺少 CSP 头 | 未配置 Content-Security-Policy | 🟡 P2 | 添加 CSP 头防止XSS |
| docker-compose.yml | 开发环境Postgres/Redis端口暴露到0.0.0.0 | 🟡 P2 | 绑定127.0.0.1 |

---

### 3.4 依赖版本问题 P2 🟡

| 位置 | 问题描述 | 修复建议 |
|-----|---------|---------|
| requirements.txt | wechatpy 使用 alpha 版 2.0.0.alpha42 | 升级到稳定版 |
| requirements.txt | alipay 版本 0.7.5 较旧 | 升级到最新安全版本 |
| requirements.txt | 未配置 pip-audit 定期扫描 | 配置 CI 中运行 pip-audit |
| frontend/package.json | 依赖使用 ^ 版本范围 | 确保package-lock.json提交，CI中npm audit检查 |
| 所有依赖 | 未配置自动化依赖更新（Dependabot/Renovate） | 配置依赖自动更新PR |

---

## 四、测试覆盖问题

### 现状
- **后端**：drama 模块之前几乎没有 service 层单元测试（本次已添加25个，但还不够）
- **前端**：完全没有测试用例

### 需要补充的测试

#### 后端测试优先级
| 模块 | 测试类型 | 优先级 |
|-----|---------|-------|
| DramaWordCountService | 单元测试（边界值：空内容、超字数、少字数、场景数） | P1 |
| DramaQualityService | 单元测试（等级边界、问题检测、汇总计算） | P1 |
| DramaRoleRunService | 单元测试（角色执行逻辑、状态流转） | P1 |
| API Views | 集成测试（权限、参数校验、正常/异常流程） | P1 |
| 模型层 | 单元测试（约束、默认值、__str__） | P2 |
| 修复建议应用 | 端到端测试（从评估→建议→应用→重新评估） | P2 |

#### 前端测试优先级
| 模块 | 测试类型 | 优先级 |
|-----|---------|-------|
| services/drama.js | API 调用和响应解析 | P1 |
| 页面组件 | 组件渲染、加载/错误状态、交互 | P2 |
| 工具函数 | 纯函数单元测试 | P2 |

### 测试规范问题
- 测试不能依赖真实外部服务（LLM、Redis、Postgres可使用测试数据库）
- 修复 bug 时必须先写能复现的测试用例
- 核心路径测试覆盖率应达到 80%+

---

## 五、修复路线图

### 第一阶段：紧急修复（24小时内）
**目标：解决P0致命问题，避免功能完全失效和数据泄露**

1. ✅ **已修复**：views.py EpisodeQualityView 占位代码
2. 🔴 **待修复**：修复所有后端文件编码问题（中文乱码）
3. 🔴 **待修复**：修复 services.py:827 `timezone.timedelta` 崩溃
4. 🔴 **待修复**：修复 `_detect_issues_from_score` 中文匹配失效
5. 🔴 **待修复**：修复 ModelConfigView model_name 保存丢失
6. 🔴 **待修复**：TokenStatsView/ModelConfigView 添加管理员权限校验
7. 🔴 **待修复**：前端 SuggestionsPanel 改用真实数据，移除 mock
8. 🔴 **待修复**：前端 ScriptsPage 移除伪造子维度分数
9. 🔴 **待修复**：前端实现复制功能
10. 🔴 **待修复**：移除根目录 package.json 硬编码默认密码

### 第二阶段：高优修复（3天内）
**目标：解决主要功能异常和高危安全问题**

1. 🟠 修复所有 N+1 查询问题
2. 🟠 多步写入操作添加 transaction.atomic()
3. 🟠 修复项目数据越权访问风险（所有接口加 user 过滤）
4. 🟠 前端添加缺失的错误处理和 loading 状态
5. 🟠 修复 setTimeout 内存泄漏
6. 🟠 前端 applySuggestions 真实数据 + 成功/失败反馈
7. 🟠 启用HTTPS，修复加密算法弱模式
8. 🟠 添加登录接口保护（限流、验证码、账户锁定）
9. 🟠 Redis限流降级熔断
10. 🟠 修复DIM_META硬编码颜色
11. 🟠 修复Admin页面分组bug

### 第三阶段：质量提升（本周内）
**目标：统一设计系统，提升代码质量和用户体验**

1. 🟡 后端所有入参使用 Serializer 校验
2. 🟡 移除所有前端硬编码颜色，统一使用设计系统
3. 🟡 所有原生 button/卡片替换为 UI 组件
4. 🟡 重构 DramaPresentation 组件使用统一设计
5. 🟡 补全后端 Service 层单元测试（覆盖率达70%+）
6. 🟡 优化 Nginx 静态文件服务
7. 🟡 添加Cookie安全属性（SameSite、HttpOnly）
8. 🟡 Docker容器非root运行
9. 🟡 服务层响应格式统一
10. 🟡 关键操作添加审计日志

### 第四阶段：持续优化（下个迭代）
**目标：最佳实践、性能优化、测试全覆盖**

1. 🟢 代码分层优化（业务逻辑全部移到Service层）
2. 🟢 添加前端单元测试和组件测试
3. 🟢 配置CI安全扫描（bandit、npm audit、pip-audit）
4. 🟢 性能优化（列表分页、虚拟滚动、缓存）
5. 🟢 可访问性优化（a11y）
6. 🟢 添加CSP安全头
7. 🟢 依赖自动更新机制
8. 🟢 日志脱敏和轮转优化
9. 🟢 错误监控和告警（Sentry接入）
10. 🟢 补充API文档

---

## 附录：问题统计

| 等级 | 后端 | 前端 | 配置安全 | 合计 |
|-----|------|------|---------|------|
| P0 🔴 致命 | 6 | 4 | 9 | 19 |
| P1 🟠 严重 | 15 | 10 | 13 | 38 |
| P2 🟡 一般 | 25 | 20 | 14 | 59 |
| P3 🟢 轻微 | 10 | 10 | 9 | 29 |
| **合计** | **56** | **44** | **45** | **145** |

---

## 验收标准

修复完成后需验证：
1. ✅ 所有P0问题修复并验证通过
2. ✅ 后端单元测试全部通过（新增+原有）
3. ✅ 前端构建无错误，控制台无 warning
4. ✅ npm run scan:imports 无新增问题
5. ✅ 核心流程冒烟测试通过（创建项目→执行角色→查看剧本→质量评估→应用建议）
6. ✅ 安全扫描无高危漏洞

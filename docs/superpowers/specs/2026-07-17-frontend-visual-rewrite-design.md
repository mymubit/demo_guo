# ScriptForge 前端视觉准重写 — 设计规格

> 状态：已批准（2026-07-17）；实现主干完成（2026-07-18，`14b9fc3`…`8e8be98`）  
> 日期：2026-07-17  
> 相关决策：Figma 非阻塞；视觉 SSOT 在本仓库；实现计划见 `docs/superpowers/plans/2026-07-17-frontend-visual-rewrite.md`  
> 验收备注：token / no-indigo 守卫全绿；全仓 `tsc`/`build` 仍被无关 WIP 挡住，见 Task 11 report

## 1. 背景与问题

当前前端（React + TypeScript + Tailwind）已具备完整业务能力，但视觉与组件层存在：

- Brand 色为 indigo（`--brand-500: #6366f1`），与「影视工台」气质不符，且落入常见 AI 产品紫系审美。
- 基础 UI 仅有 `Button` / `Badge` / `Tabs`，各页样式与密度不统一。
- `AppShell` + `PageShell` 已有骨架，但页面级布局仍偏「后台堆砌」，缺少统一的壳层/内容分工。

用户目标：系统性改观，接近**前端准重写**（视觉 + 页面层），后端契约尽量不动。

## 2. 目标与非目标

### 目标

1. 全站统一视觉语言：**影棚壳层（风格 1）+ 冷雾内容区（风格 6）**。
2. **前端准重写**：壳层、页面、通用组件按新 Design System 重做；业务 `services` / `hooks` / `types` 尽量复用。
3. 组件策略：**shadcn/ui 打底**（表单/表格/对话框等）+ **工作台模块自研**。
4. 交付形态：**方案 A** — 先 Design System，再同一大改版波次换完全部页面。
5. 设计主导：由实现方在仓库维护视觉 SSOT；产品方以「批准 / 否决 / 指出问题」参与（非设计师友好）。

### 非目标

- 不新增大功能，不做产品级信息架构大砍大改（导航分组可微调，不以新功能为驱动）。
- 不将 Figma + MCP 作为本阶段门禁（可后期补 Figma；当前 SSOT = 本规格 + token + 关键母版标注）。
- 不引入 Ant Design / MUI 等重套件。
- 不无故重写 API 层与后端。
- 不取消 PC `min-width: 1280px` 约束。

## 3. 视觉方向（已批准）

### 3.1 分层气质

| 层级 | 风格编号 | 描述 |
|------|----------|------|
| `AppShell`（侧栏、壳层高亮） | 1 影棚工台 | 深色侧栏 + 浅色主画布；信息工具感 |
| 列表 / 表格 / 表单页 | 6 冷雾工作室 | 冷灰画布、白面板、疏朗间距 |
| 工作台 | 1+6 混合 | 顶栏与阶段条偏 1 紧凑；下方画布与面板偏 6 疏朗 |

参考示意（仓库外资产，仅气质参考，非像素稿）：

- `assets/sf-mood-1-studio-console.png`
- `assets/sf-mood-6-cool-mist.png`

### 3.2 双强调色（必须严格执行）

| Token 角色 | 用途 | 禁止用于 |
|------------|------|----------|
| **accent-shell（橙金）** | 侧栏 active、壳层导航高亮、壳层级少数状态点缀 | 页内主 CTA、表单 focus 环、正文链接 |
| **accent-action（墨海军蓝）** | 页内主按钮、链接、focus ring、选中行/选中块 | 侧栏 active 底（避免侧栏变「蓝后台」） |

### 3.3 禁止项

- 紫色 / indigo 作为 brand 主色（移除现有 `brand-500: #6366f1` 体系或降为废弃别名后删除）。
- 大面积装饰性渐变、强玻璃态、多层炫光。
- 衬线展示字体作为全站标题（不做「剧本编辑室」纸感路线）。
- 英雄区堆卡片、统计条、贴纸徽章。

### 3.4 字体与密度

- 字体：无衬线，延续或等价于 `IBM Plex Sans` + `Noto Sans SC`。
- 列表页：偏疏朗（冷雾）；工作台顶区：偏紧凑；工作台主区：中等密度、分区清晰。
- 圆角：偏小到中（约 6–10px），避免 `rounded-full` 药丸簇。
- 阴影：轻或近无；优先 1px border 分层。

## 4. Design Token（规范色值）

实现时以 CSS 变量为单一来源，Tailwind `theme.extend.colors` 映射到这些变量。

```css
:root {
  /* Shell */
  --shell-bg: #0a1628;          /* navy-900 级 */
  --shell-bg-elevated: #12203a;
  --shell-ink: #e8eef7;
  --shell-ink-muted: #94a3b8;
  --accent-shell: #f4b719;      /* 橙金：仅壳层 active */
  --accent-shell-hover: #f7cb54;

  /* Canvas / content（冷雾） */
  --canvas: #eef1f5;
  --canvas-muted: #e4e9f0;
  --surface: #ffffff;
  --border: #d8dee8;

  /* Action（页内） */
  --accent-action: #0f2744;     /* 墨海军蓝主 CTA */
  --accent-action-hover: #163a66;
  --focus-ring: rgba(15, 39, 68, 0.28);

  /* Ink */
  --ink: #0f172a;
  --ink-muted: #475569;
  --ink-faint: #94a3b8;

  /* Semantic */
  --danger: #dc2626;
  --success: #159947;
  --warning: #d97706;
}
```

废弃：现有 Tailwind `brand.*` indigo 色阶；`Button` 的 `variant="brand"` 重命名或映射为 `action`（海军蓝）。壳层高亮不走 `Button` brand，而走 shell 专用样式。

`gold` 可保留为 `accent-shell` 的别名，但语义文档必须写清：金/橙 = shell，不是页内主按钮。

## 5. 组件与目录架构

```
frontend/src/
  styles/index.css          # 变量 + 基础层
  components/ui/            # shadcn 风格 primitive
  components/layout/        # AppShell, PageShell
  components/workbench/     # 自研工作台模块
  components/artifacts/     # 产物视图（换皮为主）
  components/theme/         # ThemeMatrixPicker 等
  pages/                    # 全部页面按新系统重写
  services/ hooks/ types/   # 尽量复用
```

### 5.1 shadcn 范围（应引入/重建）

至少覆盖：

- Button、Input、Textarea、Select、Checkbox、Switch
- Dialog / AlertDialog、DropdownMenu、Popover、Tooltip
- Table、Tabs、Badge、Separator、ScrollArea
- Toast（或等价通知）

主题：用上述 token 覆盖 shadcn CSS 变量；**主色绑定 `--accent-action`**，不要绑定橙。

### 5.2 自研范围（不强制 shadcn）

- `AppShell`、`PageShell`
- `PipelineRail`、`StageCanvas`、`ModulePanel`
- `GenerationJobPanel`、`GenerationTroubleCard`、`QualityLoopPanel`、`JobLlmCallLogsPanel`
- 产物视图（`ArtifactViews`、`StoryBibleView` 等）

自研模块必须消费同一套 token，禁止页面内硬编码旧 indigo。

### 5.3 Button 变体约定

| Variant | 颜色 | 场景 |
|---------|------|------|
| `action`（原 brand） | accent-action | 页内主操作 |
| `secondary` | 白底边框 | 次要操作 |
| `ghost` | 透明 | 工具条 |
| `danger` | danger | 破坏性 |
| `shell` 或弃用页内 `gold` | accent-shell | **仅**壳层/极少数品牌点缀；默认页面禁用 |

## 6. 页面清单与表现要求

| 路由 | 页面 | 气质 |
|------|------|------|
| `/login` | LoginPage | 冷雾 + 品牌展示；主按钮海军蓝；可保留轻纹理但禁止紫渐变 |
| `/projects` | ProjectListPage | 冷雾列表母版 |
| `/projects/new` | NewProjectPage | 冷雾表单 |
| `/projects/:id/settings` | ProjectSettingsPage | 冷雾表单 |
| `/projects/:id/workbench` | WorkbenchPage | 混合：紧凑顶区 + 疏朗画布 |
| `/tools/script-review` | ExternalReviewPage | 冷雾 |
| `/tools/script-review/records` | ExternalReviewRecordsPage | 冷雾表格 |
| `/admin/model` | ModelHubPage | 冷雾 |
| `/admin/llm/logs`、`/admin/llm/chains` | LlmLogsPage | 冷雾密集表格，仍用冷雾底而非全暗 |
| `/admin/config` | AdminConfigPage | 冷雾 |
| `/admin/skill-ops` | SkillOpsPage | 冷雾 |
| （布局） | AppShell / PageShell | 影棚侧栏 |

导航信息架构：默认保留现有分组（创作 / 评测工具 / 运维）；允许文案与图标微调，不以本规格驱动功能增删。

## 7. 落地波次（方案 A）

对外宣称一次大改版；对内建议按序合并（可多 commit / 多 PR，但同一里程碑）：

1. **Token + Tailwind + 全局样式** — 去掉 indigo brand，建立双强调色。
2. **shadcn primitive + Button 等** — 主题对齐 token。
3. **AppShell / PageShell** — 橙 active；冷雾主区背景。
4. **全页换装** — 建议顺序：Login → 创作域 → 工具域 → 运维域 → Workbench（或 Workbench 与创作域穿插，但必须在里程碑内完成）。
5. **清理** — 删除废弃 class、无用旧组件变体、重复面板样式。
6. **可选后续** — 将 token 与三张母版（壳层 / 列表 / 工作台）补入 Figma，再考虑 MCP。

## 8. 约束与兼容

- 技术栈：React 18、Vite、Tailwind 3、React Query、React Router、lucide-react；新增依赖优先 shadcn 所需的 Radix 生态，禁止无关 UI 库。
- 后端：`/api/v1/` 契约不变；字段命名约定不变。
- 测试：现有 vitest 组件/工具测试必须适配新 class/文案选择器后通过；关键路径补/改测试。
- PC only：`min-width: 1280px` 保留。

## 9. 验收标准

1. 全站无 indigo 主按钮/主高亮；侧栏 active 为橙金；页内主 CTA 为海军蓝。
2. 上表全部路由在新视觉下可用，核心流程手测通过：登录 → 项目列表 → 新建/进入工作台 → 外部评测 → 任一运维页。
3. `npm run typecheck`、`npm run lint`、`npm run test`（frontend）通过。
4. 工作台仍满足：顶区紧凑可扫视阶段；主区面板不拥挤到无法阅读长文本。
5. 规格中的禁止项抽查为零命中（紫 brand、衬线标题体系、装饰炫光）。

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 同一波全站改动 diff 巨大 | 按波次 1→5 提交；评审按层（token / 壳 / 域页面） |
| shadcn 默认脸过强 | 强制 token 覆盖；列表页对照冷雾母版 |
| 工作台回归难 | 保留现有 workbench 测试；手测生成任务面板与质量环 |
| 半新半旧窗口体验差 | 里程碑内尽快完成壳层后再批量换页；避免长期双主题 |

## 11. 开放项（实现前可定默认）

以下不影响本规格批准，实现计划中给默认值即可：

- shadcn 是 CLI 生成到 `components/ui` 还是手写等价 Radix 封装（默认：CLI 生成并改主题）。
- Toast 库选型（默认：跟随 shadcn 推荐）。
- 登录页是否保留轻微几何底纹（默认：可保留，但颜色改为 navy/橙低透明度，禁止紫）。

## 12. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-17 | 初稿：基于头脑风暴批准的 1+6、双色、准重写、shadcn+自研、方案 A、仓库 SSOT |

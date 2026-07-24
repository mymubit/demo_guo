# 短剧创作一体机网站 V3 设计规格

> 日期：2026-07-22  
> 产品真相源：`drama-website-design/drama-website-design.html`  
> 能力配方源：`drama-skills/`（角色 / 规则 / schema；现有 V6 operation 目录仅作内部配方）  
> 状态：**已通过**（2026-07-22）；实施计划见 `docs/superpowers/plans/2026-07-22-drama-website-v3.md`

## 1. 目标与边界

### 1.1 目标

按 HTML 产品设计，用现有技术栈**大爆炸重写**前后端产品面与编排层，交付「短剧剧本创作一体机」第一期：十大功能模块全量可用 + 套餐 UI 壳（无真实计费）。

### 1.2 已确认决策

| 决策点 | 选择 |
|--------|------|
| 产品真相源 | `drama-website-design.html`；V6 产品计划仅作历史参考，不覆盖 HTML IA |
| 第一期范围 | HTML 十大模块全量 |
| 前端策略 | React + Vite + TS 框架不变，业务代码重写 |
| 后端策略 | Django + DRF + Celery 框架不变；产品 API + 编排层（含原 v6_runtime / workbench / control_plane）按 HTML 工作流重写 |
| skills 定位 | 只作 prompt / 规则 / 契约包；不对外暴露 operation ID |
| 商业化 | 套餐展示 UI only，无支付、无配额扣减 |
| 交付方式 | 大爆炸：新 `/api/v3` + 新前端 IA；旧 `/api/v2` 与 studio 路由在第一期结束删除或不可达 |

### 1.3 明确不做（第一期）

- 真实支付、订阅扣费、配额门禁
- 多人实时协作、团队权限、剧本交易/社区/素材市场
- 换前端框架（Next.js）或换后端框架（FastAPI 等）
- 长期双栈兼容旧 V6 runtime / `/api/v2`（允许短暂停机迁移，不做双写）

## 2. 信息架构与路由

### 2.1 全局导航

| 导航 | 路由 | 对应 HTML |
|------|------|-----------|
| 创作仪表盘 | `/dashboard`（根路径 `/` 重定向至此） | 页面一 |
| 模型配置 | `/models` | 页面七 |
| 执行日志 | `/logs` | 页面八 |
| 系统配置 | `/system` | 十大模块·系统配置中心 |
| 套餐（壳） | `/billing` | 第 09 节 UI only |
| 登录 | `/login` | 现有认证保留 |

旧顶栏项（待办决策、治理实验等）不单独占一级导航；其能力并入质检流程或执行日志。

### 2.2 项目内导航

三栏范式：左导航 / 中工作区 / 右上下文。

| Tab | 路由 | HTML |
|-----|------|------|
| 概览 | `/projects/:id` | 项目卡下钻 |
| 选题定调 | `/projects/:id/topic` | 选题工作台 |
| 蓝图 | `/projects/:id/blueprint` | 页面三 |
| 分集 | `/projects/:id/episodes` | 页面四 |
| 正文编辑 | `/projects/:id/editor` | 页面二 |
| 质检 | `/projects/:id/quality` | 页面五 |
| 交付 | `/projects/:id/delivery` | 页面六 |

### 2.3 重写纪律

- 删除 `frontend/src/studio/**` 及旧路由；保留并适配 `auth`、`services/http`、测试基建
- 旧路径不双轨并存；必要时一次性重定向到新路径后删除

## 3. 全栈架构

### 3.1 保留

- 前端：React + Vite + TypeScript + TanStack Query + Tailwind
- 后端：Django + DRF + Celery + 现有认证
- 引擎内容：`drama-skills/` 只读消费

### 3.2 推倒重写

- 前端业务页、壳层、路由
- 后端产品面：`v2_views` / `v2_service` / studio 契约
- 编排面：`v6_runtime`、`v6_workbench`、`v6_control_plane`、旧 job→artifact 提交链
- 领域模型：按十模块重建（见 §4）

### 3.3 新编排原则

1. 用户动作 = 产品命令（中文业务名）
2. 命令 → 内部 plan（选角色/技能、组上下文）→ 异步执行 → 候选产物 → 校验 → 用户确认 → 提交版本
3. UI 只见业务阶段（选题 / 蓝图 / 分集 / 正文 / 质检 / 交付）；完整证据进「执行日志」
4. skills 通过加载器注入；创作者页面不出现 `create-project-brief` 等 ID（日志高级态可查看）

### 3.4 数据流

```
HTML UI → /api/v3 命令 → 新编排器 → drama-skills 加载 → LLM → 校验器 → 候选 → 确认提交 → 版本库
                              ↘ 写执行日志 / 用量事件（无计费扣减）
```

## 4. API 与领域

### 4.1 API 前缀

新建 `/api/v3/`。第一期结束后旧 `/api/v2` 返回 410 或移除路由。

| 模块 | 前缀 | 职责 |
|------|------|------|
| 项目 | `/api/v3/projects/` | 列表、创建、进度、归档 |
| 选题 | `.../topic/` | 简报生成 / 编辑 / 确认 |
| 蓝图 | `.../blueprint/` | 人物 / 世界 / 结构 / 情绪聚合 |
| 分集 | `.../episodes/` | 看板、局部修订 |
| 正文 | `.../scripts/` | 草稿、分批写、候选 diff |
| 质检 | `.../quality/` | 十维分、合规、问题接受、修复 |
| 交付 | `.../delivery/` | 门禁、打包、导出 |
| 系统配置 | `/api/v3/system/` | 题材 / 平台 / 门禁预设 |
| 模型 | `/api/v3/models/` | 供应商、密钥、角色映射 |
| 日志 | `/api/v3/logs/` | 链路、调用快照、筛选 |
| 套餐壳 | `/api/v3/billing/plans/` | 只读套餐文案 |

写操作使用幂等 command ID 与基于版本的并发控制（如 `If-Match` / base version），防止覆盖冲突。

### 4.2 核心领域对象（重建）

- `Project`：元数据、入口类型（原创/改编）、当前阶段
- `ArtifactVersion`：版本化产物、schema 版本、状态、来源运行
- `ArtifactDraft`：人工自动保存草稿（不进正式依赖图）
- `ProductCommand` / `CommandRun`：用户命令与运行主记录
- `CandidateChangeSet`：候选、差异、影响范围
- `QualityFinding`：可接受问题与处理状态
- `ContentLock`：用户锁定字段/规则
- `ExportPackage`：交付包
- `SystemConfigRevision`：系统配置修订
- `LlmProvider` / `RoleModelMapping`：模型配置
- `ExecutionLog` / `LlmCall`：执行与调用证据
- `BillingPlan`（只读配置）：套餐展示文案
- `UsageEvent`：用量事件（采集但不扣费）

结构稳定且参与查询/状态机的字段必须建模；skills 产物 payload 仍按 schema 版本存 JSON。

## 5. 十模块 ↔ skills 映射

产品命令用中文业务名；编排器内部调用 skills 配方。现有 9 个 V6 operation 目录作为能力配方迁入新编排器，不保留旧 runtime 对外契约。

| HTML 模块 | 产品命令（对外） | 内部能力配方（不暴露给创作者） | 主要产物 |
|-----------|------------------|--------------------------------|----------|
| 项目管理 | 创建 / 归档 / 进度聚合 | 无 LLM；读版本库与运行状态 | `Project` + 阶段摘要 |
| 选题定调 | 生成 / 编辑 / 确认简报 | `create-project-brief` + `drama-topic-director` | `project_brief` |
| 蓝图编辑 | 生成蓝图组、锁定、确认 | `compose-story-bible` + `drama-story-bible` | bible / character / world / emotion / originality |
| 分集画布 | 生成全剧、局部修订 | `design-episode-plan` / `revise-episode-plan` + `drama-episode-designer` | `episode_plan` |
| 正文编辑 | 分批写作、场景重写、对白建议 | `write-episodes` + `drama-script-writer` | `episode_scripts` + checkpoint |
| 质检中心 | 评分、合规、接受问题、定向修复 | `score-script` / `check-compliance` / `revise-script` + 对应角色 | quality / compliance 报告 + 新脚本版本 |
| 交付工具 | 门禁、打包、导出 | `prepare-delivery` + `drama-delivery-tool` | `production_package` + 文件 |
| 系统配置 | 题材 / 平台 / 门禁 / 公式读写 | foundation presets/rules + DB 覆盖层 | 配置修订版 |
| 模型配置 | 供应商、密钥、角色映射、试连 | provider 能力接到 `/api/v3/models` | Provider / Mapping |
| 执行日志 | 列表、链路、快照、筛选 | 编排器埋点 + LLM call 账本 | Run / Call 证据 |
| 套餐壳 | 只读套餐列表 | 静态/配置，无支付 | `plans` JSON |

## 6. 目录结构

### 6.1 前端

```
frontend/src/
  app/                 # 路由、壳、Providers
  pages/               # dashboard / login / billing / models / logs / system
  projects/            # topic / blueprint / episodes / editor / quality / delivery
  components/          # 设计系统与共享 UI
  services/            # /api/v3 客户端
  types/               # 与后端契约一致的 TS 类型
  auth/                # 保留并适配
```

### 6.2 后端

```
backend/apps/drama/
  api/v3/              # urls / views / serializers（校验与编排入口）
  domain/              # 领域模型与仓储
  orchestrator/        # command → plan → execute → candidate → commit
  skills_bridge/       # 加载 drama-skills；不暴露旧 v6_runtime API
  providers/           # 模型供应商与映射
  logging/             # 执行日志与 LLM 账本
  billing/             # 只读套餐
```

删除或停用：`v2_*`、`services/v6_runtime.py`、`v6_workbench.py`、`v6_control_plane.py` 及依赖测试。可复用的加密、LLM 适配、skills_loader、校验逻辑迁入新包后删除旧文件。

## 7. 数据迁移

1. 新建 v3 表（版本化产物、命令运行、日志、配置修订）
2. 可选一次性脚本：旧 `DramaProject` / artifact 迁入新表；迁不动标 `legacy`
3. 切流后 `/api/v2` 返回 410
4. 不保留长期双写

## 8. 第一期验收标准

1. 原创/改编均可建项 → 选题确认 → 蓝图确认 → 分集生成 → 写满至少 1 批正文（可编辑；候选确认后才落正式版）
2. 质检：质量 + 合规双报告 → 接受问题 → 定向修订 → 报告过期语义正确
3. 交付：双报告通过后可打包；未通过则阻断并说明原因
4. 模型：可配置供应商与角色映射并试连成功
5. 日志：任意一次生成可从项目动作追到输入 / 输出 / 校验结果
6. 系统配置：改平台/门禁预设后，后续运行读到新配置
7. 套餐页可展示三档文案；无支付、无配额扣减
8. 页面不出现 operation ID；旧 `/api/v2` 与旧 studio 路由在第一期结束时删除或不可达

## 9. 里程碑

| 里程碑 | 交付 | 可验收 |
|--------|------|--------|
| W0 | 契约：OpenAPI/类型、术语表、HTML→命令字典 | 契约评审通过 |
| W1 | 编排骨架 + 项目 CRUD + 仪表盘壳 | 空项目可建、导航齐 |
| W2 | 选题 + 蓝图（候选确认） | 主链前半可跑通 |
| W3 | 分集 + 正文编辑器 + 分批写 | 至少一批正文可确认落库 |
| W4 | 质检闭环 + 交付 | 验收项 2–3 |
| W5 | 系统配置 + 模型配置 + 执行日志 | 验收项 4–6 |
| W6 | 套餐壳 + 删旧 API/旧页 + 回归 | 验收全绿，v2/studio 不可达 |

工作方式：W0 先冻结 `/api/v3` 与 TS 类型；之后禁止往旧 `v2` / `v6_runtime` 加功能。每个里程碑前后端同交，不以静态页完成验收。

## 10. 测试策略（摘要）

- 后端：命令幂等、候选/提交、多产物原子提交、质检版本 join、交付门禁、LLM 失败重试取消
- 前端：路由、建项向导、编辑器自动保存、候选 diff、审稿定位、空/加载/失败态
- 端到端：原创主链、改编锁定项、写作→双报告→修订→交付、失败重试、日志追溯

## 11. 风险与接受

大爆炸期间中段前产品可能不可用。通过 W0 契约冻结与按里程碑垂直接通降低前后端假流程风险。不做长期双栈以换取 IA 与编排一致性。

## 12. 参考文档

- 产品设计：`drama-website-design/drama-website-design.html`
- 历史 V6 产品计划（仅参考）：`docs/v6-product-development-plan.md`
- 技能包：`drama-skills/`

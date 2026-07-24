# 独立剧本评审（外界剧本评分）设计

> 日期：2026-07-24  
> 状态：**已通过**（2026-07-24）；实施计划见 `docs/superpowers/plans/2026-07-24-standalone-script-review.md`  
> 背景：项目内质检闭环保留；另需全局「剧本评审」以支持外界剧本评分、历史与同剧本多次对比

## 1. 目标与边界

### 1.1 目标

提供与创作主链解耦的**剧本评审**能力：

1. 粘贴或上传外界剧本，发起**质量评分**与**合规审查**
2. 保留完整**评审记录**，支持同一评审件下多次跑分
3. 支持选两条同类型记录做**并排对比**
4. 可**可选关联**现有 V3 项目；也可纯全局使用

### 1.2 已确认决策

| 点 | 选择 |
|----|------|
| 输入 | 粘贴纯文本/Markdown **+** 上传文件 |
| 入口 | 全局独立页 **+** 可从项目跳转关联 |
| 能力范围 | 质量评分 **+** 合规审查 |
| 历史形态 | 对比向：同剧本多次评分可并排对比（第一期就要） |
| 架构方案 | **A**：独立「剧本评审」域（非影子项目、非仅工具页） |

### 1.3 第一期不做

- `.docx` 解析（仅 `.txt` / `.md`）
- 按问题自动修订、把外界稿写回项目正文
- 逐行剧本 diff（对比只做报告指标并排）
- 多人协作、公开分享链接
- 替换或削弱项目内「质检修订」页

## 2. 信息架构

### 2.1 全局导航

一级导航新增「剧本评审」→ `/reviews`（与日志、用量同级）。

| 路由 | 作用 |
|------|------|
| `/reviews` | 评审件列表 |
| `/reviews/new` | 新建（粘贴 / 上传，可选 `project_id`） |
| `/reviews/:id` | 详情：原文、触发评分/合规、记录列表 |
| `/reviews/:id/compare?a=&b=` | 两条评审记录并排对比 |

### 2.2 项目内入口

质检页（或项目设置旁）增加「用外界剧本评分」→ `/reviews/new?project_id={id}`，创建时自动关联该项目。

### 2.3 与现有质检关系

| | 项目内质检修订 | 独立剧本评审 |
|--|----------------|--------------|
| 输入 | 本项目已确认 `episode_scripts` | 外界粘贴/上传全文 |
| 产物落库 | `V3ArtifactVersion`（quality/compliance） | 仅 `ScriptReviewRun.report_payload` |
| 交付门禁 | 参与 | **不参与** |
| 执行日志 | 现有 CommandRun | 可挂 CommandRun，便于追溯 |

## 3. 主流程

1. 用户新建评审件（粘贴或上传）→ 存 `script_text`
2. 详情页触发「质量评分」和/或「合规审查」（可并行、异步）
3. 每次成功写入一条 `ScriptReviewRun`
4. 记录列表中勾选同 `kind` 最多 2 条 → 进入对比页

失败时记录 `failed` + `error_message`，不覆盖历史成功记录。

## 4. 数据模型

### 4.1 `ScriptReview`（评审件）

| 字段 | 说明 |
|------|------|
| `id` | UUID PK |
| `owner` | FK User |
| `project` | FK `V3Project`，可空 |
| `title` | 展示标题（默认可取文件名或首行） |
| `source_type` | `paste` \| `upload` |
| `source_filename` | 上传时原文件名，可空 |
| `script_text` | 归一化后的全文（评分输入） |
| `created_at` / `updated_at` | |

### 4.2 `ScriptReviewRun`（评审记录）

| 字段 | 说明 |
|------|------|
| `id` | UUID PK |
| `review` | FK ScriptReview |
| `kind` | `quality` \| `compliance` |
| `status` | `queued` \| `running` \| `succeeded` \| `failed` |
| `command_run` | FK `V3CommandRun`，可空 |
| `report_payload` | JSON，成功后的报告结构 |
| `error_message` | 失败信息 |
| `created_at` / `finished_at` | |

约束建议：同一 `review` 下允许多条同 `kind`（历史对比所需）；列表默认按时间倒序。

## 5. API（`/api/v3/reviews/`）

统一信封：`{ code: 0, message, data }`。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/reviews/` | 列表（可筛 `project_id`；仅当前用户） |
| POST | `/reviews/` | 创建：JSON（`title?`, `script_text`, `project_id?`）或 multipart（`file` + 字段） |
| GET | `/reviews/{id}/` | 详情 + runs 摘要 |
| POST | `/reviews/{id}/score/` | 触发质量评分 → 返回 run / command_run |
| POST | `/reviews/{id}/compliance/` | 触发合规审查 |
| GET | `/reviews/{id}/runs/` | 记录列表（`kind?`） |
| GET | `/reviews/{id}/runs/{run_id}/` | 单条报告详情 |
| GET | `/reviews/{id}/compare/?a={run_id}&b={run_id}` | 对比投影；要求同 `kind` 且均 `succeeded` |

### 5.1 执行约定

- 将 `script_text` 包装为临时 episode_scripts 形态，复用现有 `drama.script-scorer` / `drama.compliance-guard` 配方与系统评分预设
- **禁止**写入该项目（或任意项目）的 quality/compliance `V3ArtifactVersion`
- Token/费用走现有 LLM call log + usage 汇总
- 文件：仅允许 `.txt` / `.md`；建议上限 2MB；编码优先 UTF-8

### 5.2 对比响应投影（示例）

```json
{
  "kind": "quality",
  "left": { "run_id": "...", "created_at": "...", "summary": { "overall_score": 82, "grade": "A", "verdict": "..." }, "dimensions": [], "top_defects": [] },
  "right": { "run_id": "...", "created_at": "...", "summary": {}, "dimensions": [], "top_defects": [] },
  "deltas": { "overall_score": 4 }
}
```

合规 `kind=compliance` 时投影 `overall_result`、阻断项摘要等，无十维则 `dimensions` 为空。

## 6. 前端

### 6.1 列表 `/reviews`

- 列：标题、来源、关联项目、最近质量分、最近合规结论、更新时间
- 主 CTA：新建评审
- 空态引导粘贴/上传

### 6.2 新建 `/reviews/new`

- Tab：粘贴 | 上传
- 可选关联项目（query `project_id` 预填）
- 提交后跳转详情

### 6.3 详情 `/reviews/:id`

- 原文可折叠预览
- 按钮：质量评分、合规审查（进行中禁用并轮询）
- 记录表：多选同 kind ≤2 →「对比」
- 点单条：侧栏或子路由展示完整报告（复用质检页 DimensionBars / 问题列表等组件）

### 6.4 对比 `/reviews/:id/compare`

- 左右两栏：总分/等级、十维差、合规结论、关键缺陷摘要
- 不做剧本正文 diff

## 7. 权限与安全

- 仅 `owner` 可读写自己的评审件与 runs
- 关联 `project_id` 时须校验项目归属当前用户
- 上传文件类型与大小服务端强校验；文本入库前做长度上限（与 LLM 上下文策略对齐，超限明确报错）

## 8. 验收

1. 粘贴与上传均可创建评审件，并成功跑通质量评分与合规审查
2. 同一评审件可保留多次记录，列表可查看
3. 同 `kind` 两条成功记录可并排对比
4. 可从项目跳转并自动关联；项目内质检/交付门禁行为不变
5. 失败 run 不擦除历史成功报告；执行可在日志中追溯

## 9. 实施提示（非本文件范围）

实施计划另开 `docs/superpowers/plans/2026-07-24-standalone-script-review.md`，建议拆波次：

1. 模型 + migration + CRUD API  
2. score/compliance 异步执行桥接  
3. 前端列表/新建/详情  
4. 对比 API + 对比页 + 项目入口  

---

**自检**：无 TBD；与项目内质检边界明确；第一期文件类型与对比范围已钉死。

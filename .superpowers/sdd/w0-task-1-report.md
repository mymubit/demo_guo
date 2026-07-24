# W0 Task 1 报告：术语表与命令字典

**Status:** DONE  
**Date:** 2026-07-22  
**Task:** ScriptForge V3 W0 — 术语表与命令字典

---

## What I Implemented

### 1. `docs/contracts/v3/glossary.md`

- 创建 V3 产品术语表，包含计划要求的 8 行映射表（用户可见 ↔ 内部稳定 ID ↔ 禁止对用户说）。
- 补充简短使用说明，明确三类列的用途与边界。

### 2. `docs/contracts/v3/commands.md`

- 创建 V3 产品命令字典，包含计划指定的 15 条 `command_type` 记录（中文名、模块、异步、需确认候选）。
- 保留计划要求的说明：内部 skills 配方 ID 不进本表。
- 追加 Spec §5 十模块覆盖对照表，标注 REST-only 模块（系统配置、执行日志、套餐壳）及项目管理 REST 读操作。

---

## Verification Performed

### command_type 正则 `^[a-z][a-z0-9_]*$`

对 15 个 ID 逐一校验，全部通过：

| command_type | 通过 |
|--------------|------|
| create_project | ✓ |
| generate_topic_brief | ✓ |
| confirm_topic_brief | ✓ |
| generate_blueprint | ✓ |
| confirm_blueprint | ✓ |
| generate_episode_plan | ✓ |
| revise_episode_plan | ✓ |
| write_episode_batch | ✓ |
| confirm_script_candidate | ✓ |
| score_quality | ✓ |
| check_compliance | ✓ |
| accept_findings | ✓ |
| revise_from_findings | ✓ |
| prepare_delivery | ✓ |
| test_model_provider | ✓ |

### Spec §5 十模块覆盖

| HTML 模块 | 覆盖方式 | 状态 |
|-----------|----------|------|
| 项目管理 | `create_project` | ✓ |
| 选题定调 | `generate_topic_brief`、`confirm_topic_brief` | ✓ |
| 蓝图编辑 | `generate_blueprint`、`confirm_blueprint` | ✓ |
| 分集画布 | `generate_episode_plan`、`revise_episode_plan` | ✓ |
| 正文编辑 | `write_episode_batch`、`confirm_script_candidate` | ✓ |
| 质检中心 | `score_quality`、`check_compliance`、`accept_findings`、`revise_from_findings` | ✓ |
| 交付工具 | `prepare_delivery` | ✓ |
| 系统配置 | REST 资源，无 command | ✓（符合自检约束） |
| 模型配置 | `test_model_provider` + REST CRUD | ✓ |
| 执行日志 | REST 只读，无 command | ✓（符合自检约束） |
| 套餐壳 | REST 只读，无 command | ✓（符合自检约束） |

无遗漏；套餐无 command、系统配置用 REST 资源而非 command，与计划 Step 3 自检要求一致。

---

## Files Changed

| 路径 | 操作 |
|------|------|
| `docs/contracts/v3/glossary.md` | 新建 |
| `docs/contracts/v3/commands.md` | 新建 |
| `.superpowers/sdd/w0-task-1-report.md` | 新建（本报告） |

未修改 backend/frontend 应用代码；未执行 git commit。

---

## Self-Review

- 表值与 `docs/superpowers/plans/2026-07-22-drama-website-v3-w0-contracts.md` Task 1 逐字对齐。
- `command_type` 均为 snake_case 英文稳定 ID；中文名仅出现在「中文名」列。
- glossary 禁止列包含计划指定的 skills/operation 禁语。
- commands.md 模块列与 Spec §5 HTML 模块语义一致。
- 计划在 Step 2 仅要求核心表格 + 一行说明；覆盖对照表为辅助自检文档，不改变契约枚举。

---

## Concerns

1. **brief 文件编码**：`.superpowers/sdd/w0-task-1-brief.md` 存在乱码，实施时以计划文件 `2026-07-22-drama-website-v3-w0-contracts.md` 为准。
2. **项目管理 REST 命令边界**：Spec §5 列出「创建 / 归档 / 进度聚合」；本表仅 `create_project` 为 command，归档与进度聚合预期为 REST（Task 2+ 实现）。若后续需 `archive_project` 等 command，应在 W0 评审后追加。
3. **模型配置 CRUD**：`test_model_provider` 覆盖试连；供应商/密钥/映射的增删改查为 REST，不在本 command 表，与 Spec §4.1 `/api/v3/models/` 一致。

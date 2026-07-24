# V3 产品术语表

> 契约冻结（W0）— 创作者可见中文业务名 ↔ 内部稳定 ID 映射。  
> 供 OpenAPI、`domain.ts`、`commands.ts` 及 UI 文案引用。

## 产物与运行记录

| 用户可见 | 内部稳定 ID | 禁止对用户说 |
|----------|-------------|--------------|
| 选题定调 / 项目简报 | `project_brief` | `create-project-brief`、`operation.*` |
| 故事蓝图 | `story_bible` | `compose-story-bible` |
| 分集规划 | `episode_plan` | `design-episode-plan` |
| 剧本正文 | `episode_scripts` | `write-episodes` |
| 质量报告 | `quality_report` | `score-script` |
| 合规报告 | `compliance_report` | `check-compliance` |
| 制作交付包 | `production_package` | `prepare-delivery` |
| 运行 / 执行日志 | `command_run` | `OperationRun`（对外） |

## 使用说明

- **用户可见**：页面标题、按钮、Toast、帮助文案等面向创作者的中文业务术语。
- **内部稳定 ID**：API 字段、数据库 artifact 类型、TS 类型枚举等稳定标识，使用 snake_case。
- **禁止对用户说**：skills 配方 ID、V6 operation 目录名、内部类名等；仅出现在编排器映射表或执行日志高级态。

# 走查：注入透明性（阶段 A / §3.5）

> 对应总纲：`docs/superpowers/specs/2026-07-20-skills-optimization-program-design.md`  
> 目的：证明「一次调用 → 诊断 live → 说清 Top 层」可复现。

## 前置环境

| 项 | 说明 |
|----|------|
| 后端 | 本地或 Docker `demo_guo-backend-1`；`DRAMA_SKILLS_ROOT` 指向仓库 `drama-skills` |
| Celery | 若要**新**触发生成，需 worker 在跑；仅用历史 log 演练时可跳过 |
| LLM | `LLM_ENABLED=true` 且模型可用；否则用「已有带 injection_manifest 的调用」路径 |
| 前端 | 运维可打开 `/admin/skills` |
| 权限 | 能访问技能诊断与 LLM 日志详情 |

**无真实 LLM 时的替代路径：** 在诊断「真实注入」选一条已有 `injection_manifest ≠ null` 的记录，从步骤 2 开始。

## 五步

1. **触发或选定一次调用**  
   - 理想：工作台选题定调执行/重跑，产生新 job。  
   - 替代：诊断 → 真实注入 → 任选 topic-director 历史成功/失败调用。

2. **打开诊断 live**  
   - URL：`/admin/skills?tab=live`（可带 `&log_id=`）。  
   - 确认详情有「注入」分层 chars，而非仅全文。

3. **指认 Top3 贡献层**  
   - 写出 system 中 chars 最高的三层（如 modules / rules / knowledge）。  
   - 条件模块若有 skipped，记下一条 `reason`。

4. **干跑对照**  
   - 诊断「角色装配」选同一角色，查看干跑 vs 最近真实差异（或 Inventory 对照）。  
   - 若提示 bundle 漂移告警：不得用该条做改前/改后基线。

5. **失败深链（可选但建议）**  
   - 若有结构化失败：失败归因 →「看注入」应跳到同 `log_id`。  
   - 工作台若触发 `project_brief` 实质门禁：卡片应显示**人话** + **错误码（如 42201）**。

## 勾选记录

| 步骤 | 结果 | 日期 / 备注 |
|------|------|-------------|
| 1 触发或选定 | ☐ | |
| 2 live 注入可见 | ☐ | |
| 3 Top3 层 | ☐ | |
| 4 干跑对照 | ☐ | |
| 5 失败深链 / 门禁码 | ☐ | |

演练人：________

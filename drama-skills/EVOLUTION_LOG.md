# Drama Skills 进化日志

> 记录技能体系的**四轨道进化**历史。

---

## 四轨道进化体系

| 轨道 | 触发时机 | 内容 | 存放位置 |
|------|---------|------|---------|
| **轨道一：技能规则进化** | 评分数据低于阈值 | 更新角色SKILL.md规范 | 通过PR提交 |
| **轨道二：创作灵感归档** | 创作中随时触发 | 好的钩子/反转/对白/结构 | `inspirations/` |
| **轨道三：外部内容摄入** | 用户提交外部内容 | 从PDF/公众号/GitHub等提取知识 | `knowledge/` + `inspirations/` |
| **轨道四：新模式发现** | 拉片分析/外部摄入中发现 | 现有库未覆盖的全新规律 | `inspirations/new-patterns.md` |

提交外部内容：参见 `INTAKE_PROTOCOL.md`

---

## 技能规范进化历史

### Gen 0 · 2026-06-22 · 初始版本

**说明**：基础版本，整合以下知识资产：
- `dramaskilltrae` 分支 39 个专业技能
- `dramaskill` 分支节点系统（9个节点）
- `ai-drama-skills-v2/` 5个规范模板

**角色体系（27个角色 · 8个部门）**：
- 战略选题部：市场雷达、爆款公式师、选题策划官、立项复审官
- 世界构建部：世界架构师、人设设计师、梦境指标师
- 剧情引擎部：情节架构师、钩子设计师、冲突引擎师、反转大师、节奏设计师、心理框架师
- 创作执行部：剧本执笔师、对白专家、场景导演
- 评审质控部：审稿官、读者视角官、情绪审计官、质量报告官
- 修改润色部：修稿师、节奏优化师、格式规范师
- 制作宣发部：视觉生产官、分镜导演、营销策划官
- 合规总编室：合规守卫、进化分析师

**三分支整合清单**：
- `ScriptForge`：tier1知识区块映射、emotion_architect、ai_field_prompts
- `dramaskill`：node-9拉片分析框架、6大参考JSON库、节点系统（9节点）
- `dramaskilltrae`：39个专业技能、drama-master-suite架构

**相比前一版本（v1.0）的提升**：
- 角色数量：9个 → 29个（+情绪架构师、拉片分析师）
- 新增部门：战略选题、剧情引擎（独立6角色）、修改润色、制作宣发
- 新增能力：梦境三指标、投流切片、读者视角审查、情绪审计、QDN模型
- 进化系统：单轨（技能）→ 四轨（技能+灵感+外部摄入+新模式发现）
- 知识库：新增 knowledge/ 目录（市场洞察、知识区块索引）
- 外部摄入：支持 GitHub/PDF/公众号/小红书/Word 等任意来源

---

## 灵感归档统计

| 类型 | 初始条目数 | 最新归档日期 |
|------|-----------|------------|
| 钩子灵感 | 3 | 2026-06-22 |
| 反转灵感 | 3 | 2026-06-22 |
| 对白灵感 | 4 | 2026-06-22 |
| 结构创新 | 3 | 2026-06-22 |

---

## 待处理进化提案

> 此处记录已发现但尚未实施的改进建议

（暂无）

---

## 进化约定

1. **触发条件**：3+项目后主动复盘，或单维度连续低于70分，或用户提交外部内容
2. **最小变更**：每次最多修改3个条目（轨道一）
3. **PR审批**：所有规范变更通过PR审批（轨道一/四升级时）
4. **灵感归档**：随时可归档，无需等待批量（轨道二/三）
5. **外部摄入**：参见 `INTAKE_PROTOCOL.md`
6. **新模式升级**：3+案例验证后，提升为技能规则更新提案
7. **版本格式**：`drama-skills/evolution-gen-{N}`

---

## 外部内容摄入记录

---

### 摄入 #001 · 2026-06-22 · GitHub仓库 × 2

**来源1**：https://github.com/Shanyin-ai/shanyin-screenwriting-master（459 stars · MIT）
**来源2**：https://github.com/Shanyin-ai/shanyin-director-master（251 stars · MIT）
**作者**：@山音（AIGC艺术家/独立导演/编剧）

**提取内容摘要**：

| # | 知识类型 | 内容 | 写入位置 |
|---|---------|------|---------|
| 1 | 新方法论 | 横截面理论（电影是现实生活的横截面） | shanyin-screenwriting-methodology.md |
| 2 | 新框架 | Ghost/Lie/Flaw人物三角（补充现有欲望-恐惧-缺陷） | shanyin-screenwriting-methodology.md |
| 3 | 技能升级 | 双轨节奏系统（情节节奏×情感节奏） | shanyin-screenwriting-methodology.md |
| 4 | 技能升级 | McKee价值转变检验 | shanyin-screenwriting-methodology.md |
| 5 | 新工具 | 记忆检查点系统（防多集剧本前后矛盾） | shanyin-screenwriting-methodology.md |
| 6 | 新框架 | 选题五路径（主题/人物/空间/关系/标签碰撞） | shanyin-screenwriting-methodology.md |
| 7 | 灵感归档 | 概念组合五种方法 | inspirations/structures.md S004/S005 |
| 8 | 灵感归档 | 双轨节奏错位手法 | inspirations/structures.md S006 |
| 9 | 新知识 | 九列标准分镜表（551个真实镜头统计） | shanyin-director-methodology.md |
| 10 | 新框架 | 叙事目的双层分析（结构层+导演执行层） | shanyin-director-methodology.md |
| 11 | 新工具 | 动作-反应10种镜头变体 | shanyin-director-methodology.md |

**冲突标记**：
- 分镜格式：山音使用九列格式（含叙事目的列），我们现有格式为6列。两套格式功能不同，无矛盾，建议升级我们的分镜格式加入"叙事目的"列。
- 场景头格式：山音使用`【场景X：地点/时间】`，我们使用`集号-镜号 时间 内外 地点`。两套面向不同平台，保持并存。

**已应用**（摄入 #002，2026-06-22）：
- ✅ drama-storyboard-director v2.1：升级为九列格式，加入叙事目的列
- ✅ drama-rhythm-designer v2.1：新增双轨节奏（情节×情感）标注
- ✅ drama-script-reviewer v2.1：新增McKee价值转变检验
- ✅ drama-script-writer v2.1：加入记忆检查点触发机制

---

### 摄入 #002 · 2026-06-22 · 山音三仓库全量摄取

**来源**：
- shanyin-screenwriting-master（459 stars）— 全部参考文件（format-series/feature/short/ultrashort/core-methodology）
- shanyin-director-master（251 stars）— 全部参考文件（genre-A~F/shot-design/storyboard-format/core-methodology）
- Story-to-game（292 stars）— README+核心能力

**新增知识文件**：
- `knowledge/shanyin-series-format.md`：剧集格式完整指南（四阶段季度弧线/弧光预算/连续性追踪四表/集间节奏）
- `knowledge/shanyin-feature-format.md`：长片格式（STC15节拍/Story Circle/McKee/内在节拍+五种风格变体）
- `knowledge/shanyin-director-styles.md`：六维度导演风格模板库（是枝裕和/王家卫/希区柯克/奉俊昊等）
- `knowledge/story-to-game.md`：剧本→互动分支游戏转化工具

**技能升级（轨道一）**：
- drama-storyboard-director v2.1：六列→九列（加叙事目的列，统计数据支撑）
- drama-rhythm-designer v2.1：单轨→双轨（情节节奏×情感节奏）
- drama-script-reviewer v2.1：新增McKee价值转变检验
- drama-script-writer v2.1：新增记忆检查点机制（防多集前后矛盾）

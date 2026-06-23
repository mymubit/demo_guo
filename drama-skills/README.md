# Drama Skills — AI短剧创作技能库 v3.0

> **12个精简角色 · 8核心+4复合 · 四轴题材矩阵 · 山音方法论深度集成**
>
> v3.0 相比 v2.0 的核心变化：
> - 从 35 个角色精简到 **12 个**（删除功能重叠的旧角色，整合为 4 个复合角色）
> - 四轴题材矩阵取代固定选项（情感轴/身份轴/冲突轴/世界观，625+种组合）
> - 山音三个仓库方法论（横截面/双轨节奏/九列分镜/Ghost-Lie-Flaw）深度落地到每个角色

---

## 安装说明

| 平台 | 技能文件夹路径 | 触发方式 |
|------|--------------|---------|
| **Cursor** | `.cursor/skills/<技能名>/` | `@技能名` |
| **Codex** | `.codex/<技能名>/` | `[角色]` |
| **Trae** | 项目根目录技能文件夹 | 自然语言 |

**快速安装**：将 `drama-master/` 复制到平台技能目录，即可通过 `@drama-master` 访问所有角色。

---

## 角色架构（12个）

```
⚡ 核心必需（8个，所有项目必须执行）
◈ 增强复合（4个，按需选用）

⚡ 选题策划官     drama-topic-planner      四轴题材矩阵+横截面理论+戏剧动作公式
◈ 市场分析师     drama-market-analyst     市场分析+爆款公式+六维拉片（整合4个旧角色）
⚡ 世界架构师     drama-world-architect    世界观设定
⚡ 人设设计师     drama-character-designer Want/Need + Ghost/Lie/Flaw + 矛盾性设计
⚡ 情节架构师     drama-plot-architect     六阶段结构+分集大纲+双轨节奏
◈ 叙事工程师     drama-narrative-engineer 情绪蓝图+四级钩子+冲突升级+反转体系（整合6个旧角色）
⚡ 剧本执笔师     drama-script-writer      横截面执行+McKee价值转变+记忆检查点
⚡ 审稿官        drama-script-reviewer    格式+横截面检验+McKee完整框架+双轨节奏检验
⚡ 质量报告官    drama-quality-reporter   8维度评分（含扣分点+分集评估）
◈ 精修大师       drama-polish-master      台词AI腔检测+修稿+格式+字数+风格+九列分镜（整合7个旧角色）
◈ 制作发行师    drama-production-pack    视觉锚点+分镜+营销+交付+Story-to-Game（整合5个旧角色）
⚡ 合规守卫       drama-compliance-guard   P0/P1/P2三级合规+九维风险检测
```

---

## 快速开始

### 快速通道（8步，适合初次创作）

```
1. @drama-topic-planner  → 输入题材方向（四轴矩阵或创意），获得立项简报
2. @drama-world-architect → 世界观设定文档
3. @drama-character-designer → Ghost/Lie/Flaw人物小传
4. @drama-plot-architect → 分集大纲（双轨节奏标注）
5. @drama-script-writer episode_range=1-5 → 第1-5集剧本+记忆检查点
   @drama-script-writer episode_range=6-10 → 第6-10集... （每批5集）
6. @drama-script-reviewer → 格式+McKee+横截面+节奏全面审查
7. @drama-quality-reporter → 8维度质量评分报告
8. @drama-compliance-guard → 合规检测报告
```

### 专家通道（完整12角色）

```
选题前：@drama-market-analyst → 市场分析+爆款评估+拉片研究
大纲后：@drama-narrative-engineer → 叙事深度强化
剧本后：@drama-polish-master → 一站式精修（台词/格式/分镜）
定稿后：@drama-production-pack → 全套制作发行物料
```

---

## 四轴题材矩阵

| 维度 | 选项 |
|------|------|
| **情感轴** | 复仇爽感 / 爱情甜虐 / 治愈共鸣 / 悬疑烧脑 / 野心逐权 |
| **身份轴** | 豪门精英 / 普通女性 / 隐藏大佬 / 重生觉醒 / 跨世界者 |
| **冲突轴** | 家族内斗 / 职场博弈 / 情感纠葛 / 身份秘密 / 生存竞争 |
| **世界观** | 当代都市 / 古代宫廷 / 架空仙侠 / 近未来 / 海外异地 |

**高潜力创新组合示例（对立面法）：**

```
🔝 重生觉醒 × 复仇爽感 × 家族内斗 × 古代宫廷 → 经典爆款
💡 普通女性 × 爱情甜虐 × 身份秘密 × 当代都市 → 高代入感
✨ 治愈共鸣 × 重生觉醒 × 职场博弈 × 当代都市 → 女性成长
🔥 悬疑烧脑 × 隐藏大佬 × 情感纠葛 × 当代都市 → 甜宠×悬疑
🌟 野心逐权 × 跨世界者 × 家族内斗 × 古代宫廷 → 古装×权谋
```

---

## 核心方法论来源

| 仓库 | Stars | 核心贡献 | 落地角色 |
|------|-------|---------|---------|
| shanyin-screenwriting-master | 459⭐ | 横截面理论/戏剧动作/Ghost-Lie-Flaw/McKee/双轨节奏 | topic-planner/script-writer/character-designer/script-reviewer |
| shanyin-director-master | 251⭐ | 九列分镜/551镜头统计/叙事目的写法 | polish-master/production-pack |
| Story-to-game | 292⭐ | 剧本→互动游戏转化工具链 | production-pack |

---

## 知识库

`knowledge/` 目录包含所有专业参考资料：

```
shanyin-screenwriting-methodology.md  山音超级编剧大师方法论
shanyin-director-methodology.md       山音超级导演大师方法论
story-to-game.md                      Story-to-Game 工具链
douyin-formulas.md                    抖音爆款公式库
tier4-compliance.md                   合规红线清单
scoring-presets.md                    质量评分标准
...
```

---

## 进化日志

详见 `EVOLUTION_LOG.md`

---

*Drama Skills v3.0 · 12个角色 · 整合山音三大仓库方法论*

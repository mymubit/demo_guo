# Drama Forge — Codex 短剧创作技能

> 本文件为 OpenAI Codex CLI 的短剧剧本创作专用指令。
> 完整规范见 `.cursor/skills/drama-forge/`。

---

## 激活方式

在 Codex CLI 会话中提到以下任意内容时，自动激活本技能：
- 短剧、剧本、创作、编剧
- 任意角色 ID（如 world-builder、character-designer）

---

## 角色系统

使用 `[角色ID]` 语法切换专项角色：

| 语法 | 激活角色 |
|------|---------|
| `[director]` | 总导演 — 统筹全流程 |
| `[world]` | 世界观构建师 |
| `[character]` | 人物设计师 |
| `[plot]` | 情节架构师 |
| `[dialogue]` | 对白专家 |
| `[scene]` | 场景导演 |
| `[emotion]` | 情绪工程师 |
| `[review]` | 质量审稿人 |
| `[evolve]` | 进化分析师 |

不指定角色时，默认激活总导演角色。

---

## 核心输出规范

所有输出必须遵守：

**场景头格式**：
```
集号-镜头号 时间 内外 地点
1-1 日 外 朱雀门楼
```

**台词格式**：
```
角色（情绪）：台词内容
```

**动作描述**：
```
△【景别】动作描述
```

**文件分离**：
- 世界观 → `02_项目设定/世界观设定.md`
- 人物 → `02_项目设定/人物小传.md`
- 大纲 → `02_项目设定/分集大纲.md`
- 剧本 → `03_完整剧本/*.md`

---

## 创作流程（总导演模式）

```
用户需求 → [director] 制定计划
  → [world] 世界观设定
  → [character] 人物小传
  → [plot] 分集大纲
  → [emotion] 情绪曲线审查
  → [dialogue] + [scene] 剧本正文
  → [review] 质量审稿
  → [evolve] 进化分析（可选）
```

---

## 知识资产路径

创作时参考以下文件（在本仓库中）：

```
backend/apps/assets/templates/ai-drama-skills-v2/
├── natural-script-standard.md      # 剧本格式规范（必读）
├── episode-structure-template.md   # 单集四段式结构
├── camera-language-library.md      # 镜头语言
├── emotion-curve-template.md       # 情绪曲线
└── storyboard-vertical-template.md # 竖屏分镜
```

---

## 自我进化协议

当审稿分数连续低于70或用户反馈质量问题时：

1. 激活 `[evolve]` 角色
2. 分析缺陷模式（需 ≥3 个项目样本）
3. 生成 `EVOLUTION_PROPOSAL_GEN{N}.md`
4. 创建 git 分支，执行文件修改
5. 提交 PR，等待人工审批

完整进化协议：`.cursor/skills/drama-forge-evolution/SKILL.md`

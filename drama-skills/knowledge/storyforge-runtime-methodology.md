# StoryForge Runtime 方法论

> **来源**：https://github.com/zhiyuzi/StoryForge（5 stars · MIT · 作者 @zhiyuzi）
> **摄取时间**：2026-06-23
>
> **核心命题**：用 Harness Engineering 处理不确定性下的计算。
> 与山音方法论的区别：山音关注"怎么写好"，StoryForge 关注"如何把生成过程做成可控系统"。
> 两者互补——内容质量 + 运行时控制。

---

## 一、核心概念：不确定性下的计算

StoryForge 的关键洞察：故事生成不是普通的软件任务。

```
确定性计算（传统软件）：
  - 输入固定 → 输出唯一正确答案
  - 成功判定接近二元（通过/失败）
  
不确定性计算（内容生成）：
  - 输出不是唯一正确答案，而是多个可能成立的候选版本
  - 质量判断依赖 rubric、评审 Agent 和人工确认
  - 修正过程不保证单调提升（可能停滞/发散/振荡）
  - 人工审批是 runtime 的一级控制点，不是补丁
  - 过程留痕是后续接管/复盘的基础设施
```

**对我们系统的启示**：
- 不能用"运行一次 = 完成"的心态设计 drama 创作系统
- 每个角色的输出都是"候选版本"，需要评估回路
- 质量 gate 不是可选项，是 runtime 的核心控制结构

---

## 二、硬卡点机制（Hard Gates）

StoryForge 最重要的设计原则：**没有确认梗概，拒绝生成剧本。**

```
硬卡点位置：synopsis/approved.md

逻辑：
  if not exists("synopsis/approved.md"):
      reject("梗概尚未确认，无法生成剧本")
      return
  else:
      proceed_to_script_generation()
```

### 对 Drama Skills 的应用建议

我们的 drama 系统应设置以下硬卡点：

| 卡点 | 触发条件 | 拒绝消息 |
|------|---------|---------|
| **立项卡点** | 没有 `project_brief` 产物 | "立项简报未完成，无法开始世界构建" |
| **大纲卡点** | 没有 `series_outline` 产物 | "分集大纲未确认，无法开始剧本执笔" |
| **质量卡点** | 质量报告分数 < 75 且未人工确认 | "质量低于基准，请先确认是否继续" |
| **合规卡点** | P0/P1 合规问题未解决 | "存在合规红线，必须修改后才能交付" |

---

## 三、生成与评估角色隔离

**核心规则**：生成 Agent 和评估 Agent 必须使用不同上下文，**禁止同一 Agent 自评**。

```
StoryForge 的 Agent 分工：

生成侧（不参与评估）：
  - interviewer.md     采访 Agent
  - synopsis-generator.md  梗概生成
  - script-generator.md    剧本生成
  
评估侧（不参与生成）：
  - narrative-reviewer.md  叙事评审
  - character-reviewer.md  角色评审
  - logic-auditor.md       逻辑审计
  - format-checker.md      格式检查
```

### 在我们系统中的对应关系

```
生成侧：
  topic-planner + world-architect + character-designer + plot-architect
  + script-writer + narrative-engineer

评估侧：
  script-reviewer + quality-reporter + compliance-guard

隔离原则：
  script-writer 不能自己评估自己写的剧本
  quality-reporter 的 8 维评分必须基于独立上下文
  审稿官评估时，不加载执笔师的系统提示词
```

---

## 四、评估回路与收敛停止策略

### 收敛停机判据（最核心的设计）

StoryForge 不是"评不通过就无限重试"，而是根据**分数趋势**决定是否继续：

```
评估回路：
  生成产物 → 评估 Agent 打分 → 检查分数趋势 → 决策

四种趋势与对应动作：
  收敛（S2 > S1）：继续，但有硬上限
  停滞（S2 ≈ S1）：立即停止，交给用户
  发散（S2 < S1）：立即停止，交给用户
  振荡（有升有降）：停止，交给用户

硬上限：
  梗概：最多 3 轮自动修正
  剧本：最多 5 轮自动修正
```

### 对 Drama Skills 的应用

我们的质量 gate 应使用相同逻辑：

```python
# 伪代码：drama 系统的评估回路
def quality_gate_loop(episode, max_rounds=3):
    scores = []
    for round in range(max_rounds):
        score = quality_reporter.evaluate(episode)
        scores.append(score)
        
        if score >= 75:  # 达标
            return "pass"
        
        if len(scores) >= 2:
            trend = detect_trend(scores[-2], scores[-1])
            if trend in ["stagnant", "diverging", "oscillating"]:
                return "stop_need_human"  # 交给用户
        
        script_writer.rewrite(episode)  # 继续修正
    
    return "stop_max_rounds"  # 达到上限，交给用户
```

---

## 五、G-Eval 评分框架（先分析再打分）

StoryForge 的评分强制执行 **chain-of-thought**：

```
G-Eval 流程：
Step 1：逐集/逐场景分析（标记每个节拍的类型）
Step 2：统计计数（推进型 vs 静态型）
Step 3：基于分析给出分数（1-5分）
Step 4：说明打分理由

禁止直接打分，必须先有分析过程。
```

### 各维度评分标尺

StoryForge 的 10 维评分（比我们的 8 维更完整）：

| # | 维度 | 评估 Agent | 关键标准 |
|---|------|-----------|---------|
| ① | 格式规范 | 规范检查 | 格式错误率 FER < 5% |
| ② | 叙事效率 | 叙事评审 | 每集推进型节拍占比、无废戏 |
| ③ | 冲突处理 | 叙事评审 | 核心冲突贯穿、持续升级、反转自然 |
| ④ | 角色一致性 | 角色评审 | 对白辨识度、行为符合人设、知识边界清晰 |
| ⑤ | 情感深度 | 角色评审 | 情感弧线完整、每集 3-5 次情绪切换 |
| ⑥ | 逻辑一致性 | 逻辑审计 | 与前集和梗概完全一致 |
| ⑦ | 爽点密度 | 叙事评审 | 每集 2-3 个爽点、类型多样 |
| ⑧ | 钩子强度 | 叙事评审 | 开头 10 秒抓力、结尾 cliffhanger |
| ⑨ | 付费点优化 | 逻辑审计 | 付费墙在最大张力处、付费后立即兑现 |
| ⑩ | 赛道匹配度 | 逻辑审计 | 符合赛道核心套路 |

**我们应将 quality-reporter 的 8 维升级为这 10 维**（补充 ⑨付费点优化 和 ⑩赛道匹配度）。

---

## 六、逐集上下文加载策略（防止 Token 爆炸）

StoryForge 的关键工程设计：

```
✗ 错误方式（我们目前可能的做法）：
  生成第 50 集时加载前 49 集全文 → Token 爆炸

✓ 正确方式（StoryForge）：
  生成第 N 集时只加载：
  - 第 N-1 集全文（保证连贯）
  - 角色状态快照（当前状态，不是历史）
  - 伏笔列表（已埋/未回扣）
  - 大纲第 N 集条目（方向指引）
```

### 角色状态快照格式

这就是我们已有的"记忆检查点"！但可以进一步规范化：

```markdown
## 角色状态快照（第 N-1 集完成后）

**[主角名]**
- 当前位置：[地点]
- 情感状态：[具体描述]
- 已知信息：[关键信息列表]
- 当前 Goal：[下集驱动目标]

**伏笔清单**
- [伏笔 A]：已埋第 X 集 → 计划第 Y 集回扣
- [伏笔 B]：已埋第 X 集 → 已在第 Z 集回扣 ✓

**下集约束**
- 必须包含：[情节点]
- 必须解决：[伏笔/问题]
- 双轨节奏建议：情节[松/中/紧] × 情感[轻/中/重]
```

---

## 七、经验沉淀机制（Learned Rules）

StoryForge 的两级经验沉淀：

```
Level 1：项目级经验
  路径：projects/{project-id}/lessons.md
  触发：用户手动修改生成结果后，记录原因

Level 2：跨项目规则
  路径：knowledge/learned-rules.md
  触发：同类修改出现 2 次以上 → 提示沉淀
  效果：后续所有项目自动加载此规则
```

### StoryForge 已沉淀的五条规则（直接可用）

```
LR-001（复仇类）：
  第一集前 30 秒必须展示主角被欺压的场景
  原因：建立同情 + 愤怒，是后续爽感的基础

LR-002（甜宠类）：
  对白不超过 3 句连续的内心独白
  原因：独白破坏节奏，观众想看互动

LR-003（所有赛道）：
  付费墙前最后一集的结尾钩子必须是全剧最强的
  原因：决定用户是否付费的关键时刻

LR-004（所有赛道）：
  反派不能靠降智失败
  原因：反派太蠢 → 主角胜利含金量低 → 爽感下降

LR-005（身份反转类）：
  身份揭示场景必须有足够铺垫和仪式感
  原因：身份揭示是最大爽点，草率处理浪费高光时刻
```

---

## 八、并行分支对比机制

StoryForge 的 `/compare` 功能：

```
同一梗概 → 多个风格版本并行生成
→ 用 /compare 对比
→ 生成 comparison.md（各版本优劣对比）
→ 用户选择最优版本继续
```

**对我们系统的应用**：
- 同一集可以用不同温度（temperature）生成 2-3 个版本
- 质量报告官对比评估，推荐最优版本
- 用户确认后继续

---

## 九、主流程总结（适配 Drama Skills）

基于 StoryForge 的流程控制理念，我们的最优工作流应为：

```
1. 采访/立项
   → topic-planner（四轴矩阵+横截面理论）
   → 输出 project_brief.md

2. 梗概确认（硬卡点）
   → world-architect + character-designer + plot-architect
   → 输出 series_outline.md
   → 【必须人工确认大纲才能进入剧本阶段】

3. 叙事强化（可选）
   → narrative-engineer

4. 逐批剧本生成（每批 5 集）
   → script-writer（使用上下文加载策略：只加载上一集+快照+伏笔）
   → 输出 episode_scripts（每集附带记忆检查点）

5. 评估回路（G-Eval + 收敛停止）
   → script-reviewer（格式+McKee+横截面+节奏）
   → quality-reporter（10 维评分，分析先于打分）
   → 分数趋势检测：收敛继续/停滞立即停/发散立即停
   → 质量 < 75 分：自动修正最多 3 轮，超限交给用户

6. 精修与交付
   → polish-master
   → compliance-guard（硬卡点：P0/P1 未通过拒绝交付）
   → production-pack

7. 经验沉淀
   → 每个项目维护 lessons.md
   → 跨项目共性 → 更新 learned-rules.md
```

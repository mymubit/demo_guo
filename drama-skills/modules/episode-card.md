# 模块：标准分集卡

## 目标
把全剧阶段目标转化为正文可直接执行的单集设计。

## 输入
- `story_bible`
- 当前集所属阶段
- 前后集钩子与连续性状态

## 引用规则
- `t1.global.episode_card.required-fields`
- `t1.global.episode_structure.four-act`
- `t1.global.conflict_escalation.upgrade-protocol`

## 输出
- `narrative_plan.episode_narrative_designs[]`

## 执行步骤
1. 定义本集唯一核心事件和 Goal×Conflict。
2. 安排四段式推进与至少一次价值转变。
3. 写集首承接、集末钩子、爽点、反转和付费作用。
4. 标记伏笔埋设/回扣、人物状态变化和双轨节奏。
5. 检查下一集能否直接承接。

## 失败条件
- 一集包含多个互不服务的核心事件。
- 只写剧情摘要，不能指导场景创作。

## 自检清单
- [ ] 必填字段全部可执行
- [ ] 本集推进没有改写全剧主线
- [ ] 集末钩子与下一集首场直接连接

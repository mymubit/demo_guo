# 模块：冲突升级

> 挂载角色：`drama.story-bible`（全剧冲突链）、`drama.episode-designer`（单集对峙设计）

## 目标

按升级协议把主冲突落实为全剧冲突链，并为对峙场景提供五要素设计。

## 输入

- 全剧主冲突或当前对峙场景
- 人物诉求、权力来源与已有后果
- `series_structure` 阶段骨架（只读，不得改写）

## 引用规则

- `t1.global.conflict_escalation.four-types`
- `t1.global.conflict_escalation.upgrade-protocol`
- `t1.global.philosophy.mckee-value-shift`

冲突类型、覆盖要求和升级顺序由原子规则定义，本模块只负责落实到冲突链和场景。

## 输出

- `conflict_escalation_chain`（唯一写入者，见 `contracts/artifacts.yaml#field_writers`）
- 分集卡对峙场景五要素（episode-designer 挂载时）

story-bible 阶段写全剧冲突链；episode-designer 阶段只读全剧链、写单集对峙，禁止重写全局结构。

## 对峙场景五要素

设计任何对峙场景（吵架、谈判、摊牌）必须写明：

1. 势力对比（谁占上风，凭什么）
2. 表面诉求（台词层在争什么）
3. 真实意图（潜台词层要什么）
4. 权力拉锯（上风至少易手 1 次）
5. 场景转折（结束时价值状态与开始不同——McKee 检验）

## 执行步骤

1. 判定主冲突类型与覆盖面（四类至少覆盖 3 类）。
2. 按范围→烈度→信息→后果顺序设计升级链，每次升级换维度。
3. 对峙场景逐一写明五要素。

## 失败条件

- 升级只是同烈度重复拉扯。
- 对峙场景缺少权力易手或价值转变。

## 自检清单

- [ ] 全剧冲突链每次升级都改变了冲突质量（换维度）
- [ ] 主线冲突不能被一次对话解决
- [ ] 每个对峙场景五要素齐全
- [ ] 反派的反击有合理逻辑，禁止降智式失败（LR-004）

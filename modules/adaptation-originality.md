# 模块：改编提取与原创化

## 目标
保留来源故事的有效戏剧功能，同时形成可证明的原创人物、关系、场景和因果链。

## 输入
- `external_story`
- `adapt_notes`
- 可用的参考作品清单

## 引用规则
- `t1.global.originality.protected-elements`
- `t1.global.originality.rewrite-strategy`
- `t1.global.originality.similarity-thresholds`

## 输出
- `adapt_source.retained`
- `adapt_source.enhanced`
- `adapt_source.rewritten`
- `adapt_source.originality_check`

## 执行步骤
1. 分离抽象戏剧功能与具体受保护表达。
2. 对人物关系、场景、时机和因果链至少改动两个维度。
3. 记录保留、强化和重写依据。
4. 有工具时执行相似度检查；无工具时明确未完成数据库比对。

## 失败条件
- 仅替换姓名、地点或少量台词。
- 无检测能力却声称“原创性完全通过”。

## 自检清单
- [ ] 具体桥段和台词不存在近似复刻
- [ ] 新因果链能够独立成立
- [ ] 未完成的外部检查已明确披露

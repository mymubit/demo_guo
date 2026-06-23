// Drama Skills 可见角色中文标签（12个：8核心+4复合）
const DRAMA_AGENT_LABELS = {
  // 核心必需（快速通道）
  'drama.topic-planner': '选题策划官',
  'drama.world-architect': '世界架构师',
  'drama.character-designer': '人设设计师',
  'drama.plot-architect': '情节架构师',
  'drama.script-writer': '剧本执笔师',
  'drama.script-reviewer': '审稿官',
  'drama.quality-reporter': '质量报告官',
  'drama.compliance-guard': '合规守卫',
  // 增强复合（新角色）
  'drama.market-analyst': '市场分析师',
  'drama.narrative-engineer': '叙事工程师',
  'drama.polish-master': '精修大师',
  'drama.production-pack': '制作发行师',
};

/**
 * 获取 drama.* agent 的中文显示名。
 */
export function getDramaAgentLabel(agentId) {
  return DRAMA_AGENT_LABELS[agentId] || agentId;
}

/** 向后兼容别名 */
export function resolveAgentId(agentId) {
  return getDramaAgentLabel(agentId);
}

export { DRAMA_AGENT_LABELS };
export default getDramaAgentLabel;

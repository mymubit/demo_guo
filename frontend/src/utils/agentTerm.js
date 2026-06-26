// Drama Skills 重组后可见角色中文标签（6生产+2裁判+1工具）
const DRAMA_AGENT_LABELS = {
  'drama.topic-director': '选题定调官',
  'drama.character-relations': '人物关系官',
  'drama.series-architect': '全剧架构官',
  'drama.episode-designer': '分集设计官',
  'drama.script-writer': '剧本正文官',
  'drama.revision-master': '剧本修订官',
  'drama.script-scorer': '剧本评分官',
  'drama.compliance-guard': '合规审查官',
  'drama.delivery-tool': '宣发交付工具',
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

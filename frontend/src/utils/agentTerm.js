/**
 * Drama Skills Agent ID 工具函数
 * 
 * 所有 agent_id 均为 drama.* 格式（如 drama.plot-architect）
 */

export function resolveAgentId(row) {
  if (!row || typeof row !== 'object') return ''
  return String(row.agent_id || '').trim()
}

/** 规范化 API 响应中的 Agent ID 字段 */
export function aliasAgentFields(row) {
  if (!row || typeof row !== 'object') return row
  const agentId = resolveAgentId(row)
  if (!agentId) return row
  return { ...row, agent_id: agentId }
}

/** 从 drama.* agent_id 提取中文角色名（用于展示） */
export function getDramaAgentLabel(agentId) {
  const LABELS = {
    'drama.market-radar': '市场雷达',
    'drama.formula-analyst': '爆款公式师',
    'drama.topic-planner': '选题策划官',
    'drama.project-reviewer': '立项复审官',
    'drama.lapian-analyst': '拉片分析师',
    'drama.world-architect': '世界架构师',
    'drama.character-designer': '人设设计师',
    'drama.dream-analyst': '梦境指标师',
    'drama.emotion-architect': '情绪架构师',
    'drama.plot-architect': '情节架构师',
    'drama.hook-designer': '钩子设计师',
    'drama.conflict-engine': '冲突引擎师',
    'drama.reversal-master': '反转大师',
    'drama.rhythm-designer': '节奏设计师',
    'drama.psychology-architect': '心理框架师',
    'drama.script-writer': '剧本执笔师',
    'drama.dialogue-expert': '对白专家',
    'drama.scene-director': '场景导演',
    'drama.ip-adapter': 'IP改编师',
    'drama.script-reviewer': '审稿官',
    'drama.reader-reviewer': '读者视角官',
    'drama.emotion-auditor': '情绪审计官',
    'drama.quality-reporter': '质量报告官',
    'drama.script-editor': '修稿师',
    'drama.pacing-optimizer': '节奏优化师',
    'drama.formatter': '格式规范师',
    'drama.word-governor': '字数治理官',
    'drama.style-guardian': '风格一致性官',
    'drama.visual-producer': '视觉生产官',
    'drama.storyboard-director': '分镜导演',
    'drama.post-processor': '后期处理官',
    'drama.marketing-officer': '营销策划官',
    'drama.compliance-guard': '合规守卫',
    'drama.delivery-packer': '交付打包官',
    'drama.evolution-analyst': '进化分析师',
  }
  return LABELS[agentId] || agentId
}

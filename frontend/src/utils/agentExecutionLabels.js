/** Agent / sub-skill 执行轨迹 — 运营可读文案与合并逻辑 */

import { resolveSkillId } from '@/utils/skillTerm'

export const AGENT_ID_LABELS = {
  // drama.* 新体系（12个角色）
  
  'drama.topic-planner': '选题策划官',
  
  
  'drama.world-architect': '世界架构师',
  'drama.character-designer': '人设设计师',
  
  
  'drama.plot-architect': '情节架构师',
  
  
  
  
  
  'drama.script-writer': '剧本执笔师',
  
  
  
  'drama.script-reviewer': '审稿官',
  
  
  'drama.quality-reporter': '质量报告官',
  
  
  
  
  
  
  
  
  
  'drama.compliance-guard': '合规守卫',
  'drama.market-analyst': '市场分析师',
  'drama.narrative-engineer': '叙事工程师',
  'drama.polish-master': '精修大师',
  'drama.production-pack': '制作发行师',
  
  
}

export const SUB_SKILL_TYPE_LABELS = {
  llm: '大模型',
  cli: 'CLI 脚本',
  retrieval: '检索',
  rule: '规则',
  trace: '追踪',
}

export const EXECUTION_STATUS_LABELS = {
  executed: '已执行',
  failed: '失败',
  skipped: '已跳过',
  pending: '未跑到',
  running: '执行中',
}

export const RUN_STATUS_LABELS = {
  completed: '成功',
  failed: '失败',
  running: '执行中',
  partial: '部分成功',
  pending: '等待',
}

export function buildAgentLookup(catalog) {
  const byId = {}
  for (const a of [
    ...(catalog?.workspaceAgents || []),
    ...(catalog?.postScriptAgents || []),
    ...(catalog?.auxiliaryAgents || []),
  ]) {
    if (a?.id) byId[a.id] = a
  }
  return byId
}

export function resolveAgentDisplayName(agentId, catalog, nodeIndex) {
  if (nodeIndex != null) {
    const ws = (catalog?.workspaceAgents || []).find(
      (a) => Number(a.workspace_index) === Number(nodeIndex),
    )
    if (ws) return ws.name_zh || ws.name || agentId
  }
  const agent = buildAgentLookup(catalog)[agentId]
  if (agent) return agent.name_zh || agent.name || agentId
  return AGENT_ID_LABELS[agentId] || agentId
}

export function resolveAgentSubSkills(agentId, catalog) {
  const agent = buildAgentLookup(catalog)[agentId]
  return agent?.sub_skills || []
}

export function subSkillTypeLabel(type) {
  return SUB_SKILL_TYPE_LABELS[type] || type || '—'
}

export function executionStatusLabel(status) {
  return EXECUTION_STATUS_LABELS[status] || status || '—'
}

export function runStatusLabel(status) {
  return RUN_STATUS_LABELS[status] || status || '—'
}

/** 将 registry 定义与 artifact/DB 轨迹按 id 对齐 */
export function mergeSubSkillSteps(registrySkills = [], executionTrace = []) {
  const traceById = {}
  for (const step of executionTrace || []) {
    const id = step?.id || step?.skill_id
    if (id) traceById[id] = step
  }

  if (registrySkills?.length) {
    return registrySkills.map((def) => {
      const trace = traceById[def.id]
      return {
        id: def.id,
        label: def.description || def.id,
        type: def.type || trace?.type || '',
        status: trace?.status || 'pending',
        message: trace?.message || '',
        cli: def.cli || trace?.cli || '',
      }
    })
  }

  return (executionTrace || []).map((step) => ({
    id: step.id || step.skill_id,
    label: step.id || step.skill_id,
    type: step.type || '',
    status: step.status || 'pending',
    message: step.message || '',
    cli: step.cli || '',
  }))
}

export function summarizeSubSkillSteps(steps = []) {
  const counts = { executed: 0, failed: 0, skipped: 0, pending: 0 }
  let firstFailed = null
  for (const step of steps) {
    const key = step.status in counts ? step.status : 'pending'
    counts[key] += 1
    if (step.status === 'failed' && !firstFailed) {
      firstFailed = step
    }
  }
  return { counts, firstFailed }
}

/** 项目列表「最近执行」一行摘要 */
export function formatProjectExecutionSummary(run, catalog) {
  if (!run) return null
  const agentName = resolveAgentDisplayName(resolveSkillId(run), catalog, run.node_index)
  const nodePart = run.node_index != null ? `节点${run.node_index}` : ''
  const primary = [nodePart, agentName].filter(Boolean).join(' · ')
  if (run.status === 'failed') {
    const err = (run.error_message || '执行失败').trim()
    const short = err.length > 72 ? `${err.slice(0, 72)}…` : err
    return { primary, secondary: `失败：${short}`, tone: 'danger', runId: run.id }
  }
  return {
    primary,
    secondary: runStatusLabel(run.status),
    tone: run.status === 'completed' ? 'success' : 'default',
    runId: run.id,
  }
}

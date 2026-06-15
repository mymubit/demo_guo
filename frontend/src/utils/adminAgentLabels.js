/** Admin UI：从技能注册表 + 主链步骤解析展示名 */
import { resolveAgentId } from './agentTerm'

export function buildAgentLookup(catalog) {
  const byId = {}
  for (const a of [
    ...(catalog?.workspaceAgents || []),
    ...(catalog?.postScriptAgents || []),
    ...(catalog?.auxiliaryAgents || []),
  ]) {
    byId[a.id] = a
  }
  return byId
}

function buildIndexAgentMap(catalog) {
  const map = {}
  for (const agent of catalog?.workspaceAgents || []) {
    if (agent.workspace_index) {
      map[agent.workspace_index] = agent
    }
  }
  let nextIndex =
    Object.keys(map).length > 0 ? Math.max(...Object.keys(map).map(Number)) + 1 : 1
  for (const agentId of catalog?.post_script_chain || []) {
    const agent = buildAgentLookup(catalog)[agentId]
    if (agent && !Object.values(map).some((a) => a.id === agentId)) {
      map[nextIndex] = agent
      nextIndex += 1
    }
  }
  return map
}

/** step: 主链步骤行（含 agent_id / node_index / node_id / display_name） */
export function resolveFusionNodeAgent(step, catalog) {
  const row = typeof step === 'object' && step !== null ? step : { node_id: step }
  let agentId = resolveAgentId(row)
  if (!agentId && row.node_index != null) {
    agentId = buildIndexAgentMap(catalog)[row.node_index]?.id || ''
  }
  const byId = buildAgentLookup(catalog)
  const agent = agentId ? byId[agentId] : null
  return {
    agentId,
    agentName: agent?.name || agentId,
    agentNameZh: agent?.name_zh || agentId,
    step: row.node_index ?? null,
    nodeId: row.node_id || row.fusion_node_id || '',
  }
}

export function formatAgentStepTitle(step, catalog, fallback = '') {
  const row = typeof step === 'object' && step !== null ? step : { node_id: step }
  const info = resolveFusionNodeAgent(row, catalog)
  if (info.agentNameZh && info.step != null) {
    return `${info.step}. ${info.agentNameZh}`
  }
  return row.display_name || fallback || row.node_id || ''
}

export function formatAgentStepSubtitle(step, catalog) {
  const row = typeof step === 'object' && step !== null ? step : { node_id: step }
  const info = resolveFusionNodeAgent(row, catalog)
  if (info.agentName) {
    return `${info.agentName} · ${info.nodeId || row.node_id || ''}`
  }
  return row.node_id || ''
}

/** 将 pipeline.node.{n} / 其他 action_key 格式化为运营展示名 */
export function formatActionKeyTitle(actionKey, catalog, fallback = '') {
  const key = (actionKey || '').trim()
  const pipeMatch = /^pipeline\.node\.(\d+)$/.exec(key)
  if (pipeMatch) {
    const step = Number(pipeMatch[1])
    const agent = buildIndexAgentMap(catalog)[step]
    if (agent) {
      return `${step}. ${agent.name_zh || agent.id} (${agent.name || agent.id})`
    }
    return `步骤 ${step}`
  }
  if (key === 'pipeline.regenerate') return '重跑技能步骤'
  if (key === 'creation.submit') return '发起创作'
  if (key.startsWith('ai.generate.')) {
    const slug = key.replace('ai.generate.', '').replace(/_/g, ' ')
    return `字段 AI · ${slug}`
  }
  return fallback || key
}

const LLM_SOURCE_TYPE_LABELS = {
  node: '融合节点',
  agent: '辅助 Agent',
  ai_field: 'AI 字段',
  test: '连通测试',
  other: '其他',
}

function humanizeFusionNodeKey(sourceKey) {
  const key = String(sourceKey || '').trim()
  const base = key.split(':')[0]
  const match = /^node-(\d+)-(.+)$/i.exec(base)
  if (match) {
    const step = match[1]
    const slug = match[2].replace(/-/g, ' ')
    return `步骤 ${step} · ${slug}`
  }
  return base
}

/** Dashboard：LLM 调用来源展示名 */
export function formatLlmSourceLabel(sourceType, sourceKey, catalog = null) {
  const typeLabel = LLM_SOURCE_TYPE_LABELS[sourceType] || sourceType
  const key = String(sourceKey || '').trim()
  let keyLabel = key
  if (sourceType === 'node') {
    keyLabel = humanizeFusionNodeKey(key)
  } else if (sourceType === 'ai_field') {
    keyLabel = formatActionKeyTitle(key, catalog, key)
  } else if (sourceType === 'agent') {
    const agentId = key.split(':')[0]
    const agent = buildAgentLookup(catalog || {})[agentId]
    keyLabel = agent?.name_zh || agent?.name || agentId || key
  }
  return `${typeLabel} · ${keyLabel}`
}

/** Admin：缩短 SSOT 磁盘路径，避免暴露本机绝对路径 */
export function formatSkillRootDisplay(skillRoot) {
  if (!skillRoot) return ''
  const normalized = String(skillRoot).replace(/\\/g, '/')
  const marker = 'short-drama-script-creator'
  const idx = normalized.indexOf(marker)
  if (idx >= 0) return normalized.slice(idx)
  const parts = normalized.split('/').filter(Boolean)
  if (parts.length >= 2) return parts.slice(-2).join('/')
  return parts[0] || normalized
}

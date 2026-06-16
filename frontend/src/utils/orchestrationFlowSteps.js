/**
 * 流程画布：将 Outline / Script 主链步骤展开为同级 LLM 子执行节点（与立项/人设/结构同一视觉层级）。
 */
export const AGENT_LLM_SUB_FLOW = {
  outline: [
    { key: 'outline_framework', label: '大纲框架', subSkillId: 'framework-builder' },
    { key: 'outline_episode', label: '逐集集纲', subSkillId: 'episode-outline-writer' },
  ],
  script: [
    { key: 'script_batch', label: '分批剧本', subSkillId: 'episode-script-writer' },
    { key: 'from-outline-expander', label: '大纲扩写', subSkillId: 'from-outline-expander' },
  ],
}

const SUB_FLOW_AGENT_IDS = new Set(Object.keys(AGENT_LLM_SUB_FLOW))

export function isSubFlowNodeId(nodeId) {
  return String(nodeId || '').includes('::')
}

export function parseSubFlowNodeId(nodeId) {
  const raw = String(nodeId || '')
  const sep = raw.indexOf('::')
  if (sep <= 0) return { parentNodeId: raw, subFlowKey: '' }
  return {
    parentNodeId: raw.slice(0, sep),
    subFlowKey: raw.slice(sep + 2),
  }
}

export function resolveFlowSelectionNodeId(nodeId, steps = []) {
  if (!isSubFlowNodeId(nodeId)) return nodeId
  const { parentNodeId } = parseSubFlowNodeId(nodeId)
  return steps.some((s) => s.node_id === parentNodeId) ? parentNodeId : nodeId
}

function subFlowLabel(step, subFlow) {
  return subFlow.label || subFlow.key
}

/**
 * 将 pipeline steps 展开：outline / script 各拆为 2 个同级画布节点。
 */
export function expandFlowSteps(steps = []) {
  const ordered = [...steps].sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0))
  const expanded = []
  let order = 1

  for (const step of ordered) {
    const agentId = String(step.agent_id || '').trim()
    const subFlows = AGENT_LLM_SUB_FLOW[agentId]

    if (!subFlows?.length) {
      expanded.push({
        ...step,
        flow_order: order,
        is_sub_flow: false,
      })
      order += 1
      continue
    }

    for (const subFlow of subFlows) {
      expanded.push({
        ...step,
        node_id: `${step.node_id}::${subFlow.key}`,
        parent_node_id: step.node_id,
        display_name: subFlowLabel(step, subFlow),
        agent_name_zh: subFlowLabel(step, subFlow),
        sub_flow_key: subFlow.key,
        sub_skill_id: subFlow.subSkillId,
        llm_route_key: subFlow.key,
        flow_order: order,
        is_sub_flow: true,
        chain_order: order,
      })
      order += 1
    }
  }

  return expanded
}

export function agentHasSubFlow(agentId) {
  return SUB_FLOW_AGENT_IDS.has(String(agentId || '').trim())
}

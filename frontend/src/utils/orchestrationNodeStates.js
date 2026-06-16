/** 编排节点运行态：idle / running / completed / failed */
export const NODE_RUN_STATES = {
  idle: {
    label: '待执行',
    dot: 'bg-navy-500',
    ring: 'border-white/10',
    text: 'text-navy-400',
    badge: 'bg-slate-800/60 text-navy-300 border-white/10',
  },
  running: {
    label: '执行中',
    dot: 'bg-cyan-400 animate-pulse',
    ring: 'border-cyan-400/50 shadow-[0_0_12px_rgba(34,211,238,0.25)]',
    text: 'text-cyan-300',
    badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  },
  completed: {
    label: '已完成',
    dot: 'bg-green-400',
    ring: 'border-green-500/35',
    text: 'text-green-300',
    badge: 'bg-green-500/15 text-green-300 border-green-500/30',
  },
  failed: {
    label: '失败',
    dot: 'bg-red-400',
    ring: 'border-red-500/40',
    text: 'text-red-300',
    badge: 'bg-red-500/15 text-red-300 border-red-500/30',
  },
}

export function resolveNodeRunState(nodeStates, nodeId) {
  if (!nodeId || !nodeStates) return 'idle'
  return nodeStates[nodeId] || 'idle'
}

export function agentIdToNodeId(steps, agentId) {
  if (!agentId || !steps?.length) return ''
  const hit = steps.find((s) => s.agent_id === agentId || s.node_id === agentId)
  return hit?.node_id || ''
}

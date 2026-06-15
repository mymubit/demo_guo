/** 主链 Agent ID：API 响应以 agent_id 为准 */

/** 解析 Admin / 主链 API 返回的废弃字段说明 */
export function readDeprecatedAgentFields(payload) {
  return payload?.api_meta?.deprecated_fields || {}
}

export function resolveAgentId(row) {
  if (!row || typeof row !== 'object') return ''
  return String(row.agent_id || '').trim()
}

/** 规范化主链行 Agent ID 字段 */
export function aliasAgentFields(row) {
  if (!row || typeof row !== 'object') return row
  const agentId = resolveAgentId(row)
  if (!agentId) return row
  return {
    ...row,
    agent_id: agentId,
  }
}

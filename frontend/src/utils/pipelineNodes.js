/** 创作主链展示：优先读 portal_visible；无字段时沿用旧 fusion_node_id 兜底 */
export function filterCreationPipelineNodes(nodes) {
  return (nodes || []).filter((n) => {
    if (n.portal_visible === false) return false
    if (n.portal_visible === true) return true
    const fid = String(n.fusion_node_id || '')
    if (fid === 'node-8-score' || fid === 'node-6-review') return false
    return true
  })
}

export function isScoringPipelineNode(node) {
  const fid = String(node?.fusion_node_id || '')
  if (fid === 'node-8-score') return true
  return String(node?.name || '').includes('评分')
}

/** C 端步骤名：去掉「节点」后缀 */
export function displayPipelineStepName(name) {
  return String(name || '')
    .replace(/节点$/g, '')
    .trim()
}

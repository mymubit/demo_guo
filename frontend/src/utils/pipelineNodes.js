/** Creation main-chain display helpers. Runtime now exposes only ScriptForge's 5 nodes. */
export function filterCreationPipelineNodes(nodes) {
  return (nodes || []).filter((n) => n.portal_visible !== false)
}

export function isScoringPipelineNode(node) {
  return String(node?.name || '').includes('评分')
}

/** C-side step name: trim the legacy "节点" suffix when present. */
export function displayPipelineStepName(name) {
  return String(name || '')
    .replace(/节点$/g, '')
    .trim()
}

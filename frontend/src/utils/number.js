export function safeNumber(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

/** 节点/定价项币价（兼容 coinCost / coin_cost） */
export function nodeCoinCost(node) {
  if (!node) return 0
  const raw = node.coinCost ?? node.coin_cost
  return safeNumber(raw, 0)
}

/** 逐集 gate 通过率（兼容 passRate 缺失） */
export function gatePassRate(summary) {
  if (!summary) return 0
  if (Number.isFinite(summary.passRate)) return summary.passRate
  const total = safeNumber(summary.total, 0)
  const passed = safeNumber(summary.passed, 0)
  if (total <= 0) return 0
  return Math.round((passed / total) * 1000) / 10
}

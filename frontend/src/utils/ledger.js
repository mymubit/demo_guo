/** 流水展示 — 优先使用后端 description / category */

const CATEGORY_STYLES = {
  失败退还: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
  会员赠送: 'bg-purple-500/15 text-purple-300 border-purple-500/25',
  注册赠送: 'bg-green-500/15 text-green-300 border-green-500/25',
  充值到账: 'bg-green-500/15 text-green-300 border-green-500/25',
  收入: 'bg-green-500/15 text-green-300 border-green-500/25',
  'AI 消耗': 'bg-red-500/15 text-red-300 border-red-500/25',
  创作节点: 'bg-red-500/15 text-red-300 border-red-500/25',
  发起创作: 'bg-red-500/15 text-red-300 border-red-500/25',
  消耗: 'bg-red-500/15 text-red-300 border-red-500/25',
}

export function ledgerRowDescription(row) {
  if (row?.description) return row.description
  if (row?.remark) return row.remark
  return row?.action_key || '—'
}

export function ledgerRowCategory(row) {
  return row?.category || (row?.delta > 0 ? '收入' : '消耗')
}

export function ledgerCategoryClass(category) {
  return CATEGORY_STYLES[category] || 'bg-navy-800/60 text-navy-300 border-navy-600/30'
}

export function formatLedgerDelta(delta) {
  const n = Number(delta) || 0
  return `${n > 0 ? '+' : ''}${n}`
}

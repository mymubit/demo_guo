/** 后台三层经济口径（统一文案） */

export const ECONOMICS = {
  rmbRevenue: {
    label: '人民币收入',
    desc: '充值、会员订单的真实到账金额（元）',
  },
  creationCoins: {
    label: '创作币',
    desc: '站内虚拟经济；扣费、发放、余额不等于人民币收入或 API 成本',
  },
  llmCost: {
    label: 'LLM 成本',
    desc: '大模型 API 真实支出（元），按 Token 单价估算',
  },
}

export const COMMERCE_PAGE_NOTE =
  '充值档位「价格(元)」为人民币收款；到账的创作币为站内虚拟币。LLM Token 真实 API 成本在 Dashboard「大模型成本」单独核算。'

export const ORDERS_PAGE_NOTE =
  '本页均为人民币订单（充值 / 会员）。到账创作币见用户钱包；大模型 API 成本见 Dashboard「大模型成本」。'

export const COIN_PRICING_NOTE =
  '此处扣费单位为创作币（站内经济），与 Dashboard「大模型成本」中的 Token API 成本（人民币）不是同一概念。'

export const LLM_PRICING_NOTE =
  'Token 单价用于 Dashboard「大模型成本」核算 API 真实支出（元），与主链/填表的创作币扣费无关。'

/** 根据原价与折扣计算实付（元），与后端 commerce_pricing 一致 */
export function resolveChargePriceYuan({ original, discountPercent, manualPrice }) {
  const discount = Number(discountPercent)
  const orig = Number(original)
  const manual = Number(manualPrice)
  if (orig > 0 && discount > 0 && discount < 100) {
    return Math.round(orig * discount) / 100
  }
  return Number.isFinite(manual) ? manual : 0
}

/** 折扣 < 100 且有划线原价时，实付由系统计算 */
export function isAutoChargePrice(discountPercent, original) {
  const discount = Number(discountPercent)
  const orig = Number(original)
  return orig > 0 && Number.isFinite(discount) && discount > 0 && discount < 100
}

export function formatChargeYuanInput(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  return n % 1 === 0 ? String(Math.round(n)) : n.toFixed(2)
}

/** 根据原价/折扣同步实付；无有效折扣时保留 manualPrice */
export function syncChargeFromDiscount({ original, discountPercent, manualPrice }) {
  if (isAutoChargePrice(discountPercent, original)) {
    return formatChargeYuanInput(
      resolveChargePriceYuan({ original, discountPercent, manualPrice: 0 })
    )
  }
  return formatChargeYuanInput(manualPrice ?? 0)
}

export function discountDisplayLabel(discountPercent) {
  const discount = Number(discountPercent)
  if (!Number.isFinite(discount) || discount >= 100) return null
  const zhe = discount / 10
  const text = zhe.toFixed(1).replace(/\.0$/, '')
  return `${text}折`
}

export function formatPricePreview({ original, discountPercent, manualPrice }) {
  const charge = resolveChargePriceYuan({ original, discountPercent, manualPrice })
  const label = discountDisplayLabel(discountPercent)
  if (label && Number(original) > 0) {
    return `实付 ¥${charge.toFixed(2)}（${label}，原价 ¥${Number(original).toFixed(2)}）`
  }
  return `实付 ¥${charge.toFixed(2)}`
}

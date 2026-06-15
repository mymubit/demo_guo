function parseYuanValue(value) {
  if (value == null || value === '') return null
  if (typeof value === 'string') {
    const cleaned = value.replace(/[¥￥]/g, '').trim()
    const n = Number(cleaned)
    return Number.isFinite(n) ? n : null
  }
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function formatYuanNumber(value) {
  const n = parseYuanValue(value)
  if (n == null) return null
  return n % 1 === 0 ? String(Math.round(n)) : n.toFixed(2).replace(/\.?0+$/, '')
}

function resolveDiscountLabel(discountLabel, discountPercent) {
  if (discountLabel) return discountLabel
  const discount = Number(discountPercent)
  if (!Number.isFinite(discount) || discount >= 100) return null
  const zhe = discount / 10
  return `${zhe.toFixed(1).replace(/\.0$/, '')}折`
}

function resolveOriginalNum({ originalPrice, displayOriginalPrice, chargeNum, discountPercent }) {
  const fromApi = formatYuanNumber(displayOriginalPrice ?? originalPrice)
  if (fromApi) return fromApi

  const charge = parseYuanValue(chargeNum)
  const discount = Number(discountPercent)
  if (charge && discount > 0 && discount < 100) {
    return formatYuanNumber((charge * 100) / discount)
  }
  return null
}

/**
 * 会员/充值价格展示
 * layout=stack：会员卡片（垂直层次）
 * layout=compact：充值档位（紧凑）
 */
export default function PriceWithDiscount({
  price,
  displayPrice,
  originalPrice,
  displayOriginalPrice,
  discountLabel,
  discountPercent,
  validityDays,
  subline,
  size = 'md',
  suffix = null,
  chargeTone = 'white',
  layout = 'compact',
  framed = false,
  className = '',
}) {
  const chargeNum = formatYuanNumber(displayPrice ?? price)
  const label = resolveDiscountLabel(discountLabel, discountPercent)
  const originalNum = resolveOriginalNum({
    originalPrice,
    displayOriginalPrice,
    chargeNum,
    discountPercent,
  })

  const charge = parseYuanValue(chargeNum)
  const original = parseYuanValue(originalNum)
  const showPromo = Boolean(label && original && original > charge)

  const heroSize =
    size === 'lg'
      ? 'text-[2.75rem] sm:text-5xl'
      : size === 'sm'
        ? 'text-2xl'
        : 'text-4xl'
  const chargeColor = chargeTone === 'gold' ? 'text-gold-400' : 'text-white'

  const computedSubline =
    subline ??
    (validityDays > 0 && charge
      ? `约 ${(charge / validityDays).toFixed(2)} 元/天`
      : null)

  if (!chargeNum) return null

  const suffixText = suffix ? suffix.replace(/^\//, '') : null

  const content =
    layout === 'stack' ? (
      <div className="space-y-3">
        {(computedSubline || showPromo) && (
          <div className="flex items-center justify-between gap-2 min-h-[1.25rem]">
            {computedSubline ? (
              <span className="text-xs text-navy-400 tabular-nums">{computedSubline}</span>
            ) : (
              <span />
            )}
            {showPromo ? (
              <span className="inline-flex shrink-0 items-center rounded-full border border-red-500/25 bg-red-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-red-400">
                限时{label}
              </span>
            ) : null}
          </div>
        )}

        <div className={`flex items-baseline gap-1 ${chargeColor}`}>
          <span className={`${heroSize} font-bold tabular-nums leading-none tracking-tight`}>
            {chargeNum}
          </span>
          <span className="text-base text-navy-300 font-medium pb-0.5">
            元{suffixText ? `/${suffixText}` : ''}
          </span>
        </div>

        {showPromo ? (
          <p className="text-sm text-navy-500">
            原价
            <span className="ml-1 line-through tabular-nums">¥{originalNum}</span>
          </p>
        ) : null}
      </div>
    ) : (
      <div className="space-y-1.5">
        {computedSubline ? (
          <div className="text-[11px] sm:text-xs text-navy-400 tabular-nums">{computedSubline}</div>
        ) : null}
        <div className={`flex items-baseline gap-0.5 ${chargeColor}`}>
          <span className={`${heroSize} font-bold tabular-nums leading-none`}>{chargeNum}</span>
          <span className="text-base font-bold">元</span>
        </div>
        {showPromo ? (
          <p className="text-xs text-navy-400">
            原价
            <span className="mx-1 line-through text-navy-500">¥{originalNum}</span>
            <span className="text-red-400 font-semibold">限时{label}</span>
          </p>
        ) : null}
      </div>
    )

  if (framed) {
    return (
      <div
        className={`rounded-2xl border border-navy-700/40 bg-navy-900/35 px-4 py-4 ${className}`}
      >
        {content}
      </div>
    )
  }

  return <div className={className}>{content}</div>
}

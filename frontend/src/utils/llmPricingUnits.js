/** 火山/国内控制台常用「元/千 Token」；后端存储「元/百万 Token」便于高精度计算。 */

export const LLM_RECOMMENDED_PRESET_KEYS = new Set([
  'ark-deepseek-v4-flash',
  'ark-deepseek-v4-pro',
  'glm-5',
  'doubao-seed-2.0-lite',
])

export function perThousandToPerMillion(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return ''
  return (n * 1000).toFixed(4).replace(/\.?0+$/, '')
}

export function perMillionToPerThousand(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return ''
  return (n / 1000).toFixed(6).replace(/\.?0+$/, '')
}

/** 将后端百万单价格式化为「元/千」展示文案 */
export function formatPricingPairPerThousand(inputPerMillion, outputPerMillion) {
  const inp = perMillionToPerThousand(inputPerMillion)
  const out = perMillionToPerThousand(outputPerMillion)
  if (!inp && !out) return null
  return `输入 ${inp || '—'} / 输出 ${out || '—'} 元/千 Token`
}

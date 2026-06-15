/** 安全解析时间为毫秒时间戳，无效则 null */
export function parseDateMs(value) {
  if (value == null || value === '') return null
  const ms = new Date(value).getTime()
  return Number.isFinite(ms) ? ms : null
}

/** YYYY-MM-DD HH:mm */
export function formatDateTime(value, fallback = '—') {
  if (!value) return fallback
  const ms = parseDateMs(value)
  if (ms == null) {
    const s = String(value)
    if (s.length >= 16) return s.slice(0, 16).replace('T', ' ')
    if (s.length >= 10) return s.slice(0, 10)
    return fallback
  }
  const d = new Date(ms)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** YYYY-MM-DD */
export function formatDate(value, fallback = '—') {
  if (!value) return fallback
  const ms = parseDateMs(value)
  if (ms == null) {
    const s = String(value)
    return s.length >= 10 ? s.slice(0, 10) : fallback
  }
  const d = new Date(ms)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** 距今天数（无效日期返回 0） */
export function daysUntil(value) {
  const ms = parseDateMs(value)
  if (ms == null) return 0
  return Math.max(0, Math.ceil((ms - Date.now()) / (1000 * 60 * 60 * 24)))
}

/** 优先 API remaining_days，否则从 end_at 计算 */
export function resolveRemainingDays(info) {
  if (!info) return 0
  if (typeof info.remaining_days === 'number' && Number.isFinite(info.remaining_days)) {
    return Math.max(0, info.remaining_days)
  }
  const expiry = info.end_at
  return expiry ? daysUntil(expiry) : 0
}

/** 合并 /me 与 /summary 会员字段 */
export function mergeMembershipState(membership, summary, fallback = {}) {
  const merged = membership ? { ...membership } : { ...fallback }
  if (!summary) return merged
  if (summary.wallet) merged.wallet = summary.wallet
  if (typeof summary.remaining_days === 'number' && Number.isFinite(summary.remaining_days)) {
    merged.remaining_days = summary.remaining_days
  }
  if (summary.end_at) merged.end_at = summary.end_at
  if (summary.plan_name) merged.plan_name = summary.plan_name
  if (summary.is_active !== undefined) merged.is_active = summary.is_active
  return merged
}

const SENSITIVE_KEYS = ['password', 'token', 'authorization', 'cookie', 'secret', 'api_key', 'refresh', 'access']
const PHONE_RE = /(^|[^\d])(1[3-9]\d{9})(?!\d)/g
const EMAIL_RE = /([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})/g

function isSensitiveKey(key) {
  const normalized = String(key || '').toLowerCase()
  return SENSITIVE_KEYS.some((item) => normalized.includes(item))
}

function maskString(value, maxLength = 1000) {
  let text = String(value)
  if (text.length > maxLength) text = `${text.slice(0, maxLength)}...<truncated>`
  text = text.replace(PHONE_RE, (_, prefix, phone) => `${prefix}${phone.slice(0, 3)}****${phone.slice(-4)}`)
  return text.replace(EMAIL_RE, (_, prefix, domain) => `${prefix}***${domain}`)
}

export function sanitizePayload(value, depth = 0) {
  if (depth > 4) return '<max_depth>'
  if (value == null || typeof value === 'boolean' || typeof value === 'number') return value
  if (typeof value === 'string') return maskString(value)
  if (Array.isArray(value)) return value.slice(0, 50).map((item) => sanitizePayload(item, depth + 1))
  if (typeof value === 'object') {
    return Object.entries(value)
      .slice(0, 50)
      .reduce((acc, [key, item]) => {
        acc[String(key).slice(0, 80)] = isSensitiveKey(key) ? '***' : sanitizePayload(item, depth + 1)
        return acc
      }, {})
  }
  return maskString(value)
}

export function payloadSize(value) {
  try {
    return new Blob([JSON.stringify(value)]).size
  } catch {
    return 0
  }
}

export function normalizeError(error) {
  if (!error) return { message: 'Unknown error' }
  if (error instanceof Error) {
    return {
      error_type: error.name || 'Error',
      message: error.message || String(error),
      stack: error.stack || '',
    }
  }
  if (typeof error === 'object') return sanitizePayload(error)
  return { message: maskString(error) }
}

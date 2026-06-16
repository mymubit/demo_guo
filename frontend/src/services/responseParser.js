import { API_SUCCESS_CODE } from './constants/errorCodes'

/** 解包后端 { code, message, data, pagination? } 信封 */
export function unwrapApiEnvelope(raw) {
  if (!raw || typeof raw !== 'object') {
    return { ok: true, value: raw }
  }
  if (typeof raw.code !== 'number') {
    return { ok: true, value: raw }
  }
  if (raw.code === API_SUCCESS_CODE) {
    if (raw.pagination != null) {
      return { ok: true, value: { data: raw.data, pagination: raw.pagination } }
    }
    return { ok: true, value: raw.data }
  }
  return {
    ok: false,
    code: raw.code,
    message: raw.message,
    data: raw.data,
  }
}

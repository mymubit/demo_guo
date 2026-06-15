const TECHNICAL_PATTERNS = [
  /HTTPSConnectionPool/i,
  /ConnectionPool/i,
  /NameResolutionError/i,
  /Traceback/i,
  /urllib3/i,
  /requests\.exceptions/i,
  /ECONNREFUSED/i,
  /ETIMEDOUT/i,
  /socket\.gaierror/i,
  /Network Error/i,
  /AxiosError/i,
  /Failed to fetch/i,
  /\bFile "[^"]+", line \d+/,
]

/**
 * 将 API / 网络底层异常转为用户可读文案；已是中文业务提示则原样返回。
 */
export function formatUserError(raw, fallback = '操作失败，请稍后重试') {
  if (raw == null || raw === '') return fallback
  let msg = String(raw).trim()
  msg = msg
    .replace(/^LLM 请求失败:\s*/i, '')
    .replace(/^Error:\s*/i, '')
    .replace(/^服务器内部错误:\s*/i, '')
    .replace(/^读取 LLM 配置失败:\s*/i, '')

  if (!msg) return fallback

  if (TECHNICAL_PATTERNS.some((pattern) => pattern.test(msg))) {
    if (/example\.com/i.test(msg)) {
      return '无法连接模型服务：请检查 Base URL 是否为真实地址（勿使用 api.example.com 示例），并确认 API Key 正确。'
    }
    return fallback
  }

  if (msg.length > 200) {
    return `${msg.slice(0, 200)}…`
  }
  return msg
}

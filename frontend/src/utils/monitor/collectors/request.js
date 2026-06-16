import { enqueueMonitorEvent, getMonitorConfig } from '../client'

let installed = false

function shouldSkip(url) {
  const config = getMonitorConfig()
  return config.ignoreUrls?.some((item) => String(url || '').includes(item))
}

function readBusinessCode(body) {
  if (!body || typeof body !== 'object') return 0
  const code = body.code
  return typeof code === 'number' ? code : 0
}

function emitApiMonitorEvent(response) {
  const config = response.config || {}
  const startedAt = config.metadata?.monitorStartedAt
  if (startedAt == null || shouldSkip(config.url)) {
    return response
  }

  const body = response.data
  const businessCode = readBusinessCode(body)
  const durationMs = Math.round(performance.now() - startedAt)
  const traceId = response.headers?.['x-trace-id'] || ''

  if (businessCode !== 0) {
    enqueueMonitorEvent({
      type: 'api_business_error',
      level: businessCode >= 500 ? 'error' : 'warning',
      name: 'api_business_error',
      message: body?.message || '业务请求失败',
      trace_id: traceId,
      payload: {
        method: config.method,
        url: config.url,
        status: response.status,
        code: businessCode,
        duration_ms: durationMs,
        params: config.params,
        response: {
          code: businessCode,
          message: body?.message,
        },
      },
    })
    return response
  }

  enqueueMonitorEvent({
    type: 'custom',
    level: response.status >= 400 ? 'warning' : 'info',
    name: 'api_request',
    trace_id: traceId,
    payload: {
      method: config.method,
      url: config.url,
      status: response.status,
      duration_ms: durationMs,
      params: config.params,
    },
  })
  return response
}

export function installAxiosMonitor(instance) {
  if (installed || !instance?.interceptors) return
  installed = true
  instance.interceptors.request.use((config) => {
    if (!shouldSkip(config.url)) {
      config.metadata = { ...(config.metadata || {}), monitorStartedAt: performance.now() }
    }
    return config
  })
  instance.interceptors.response.use(
    (response) => emitApiMonitorEvent(response),
    (error) => {
      const config = error?.config || {}
      const startedAt = config.metadata?.monitorStartedAt
      if (startedAt != null && !shouldSkip(config.url)) {
        const businessCode = error.code ?? error.response?.data?.code
        const isBusinessError =
          typeof businessCode === 'number' &&
          businessCode !== 0 &&
          (error.response?.status === 200 || !error.response?.status)
        enqueueMonitorEvent({
          type: isBusinessError ? 'api_business_error' : 'api_error',
          level: 'error',
          name: isBusinessError ? 'api_business_error' : 'api_error',
          message: error.message || '接口请求异常',
          trace_id: error.response?.headers?.['x-trace-id'] || '',
          payload: {
            method: config.method,
            url: config.url,
            status: error.response?.status,
            code: businessCode,
            duration_ms: Math.round(performance.now() - startedAt),
            params: config.params,
            request: config.data,
            response: error.response?.data ?? { code: businessCode, message: error.message },
          },
        })
      }
      return Promise.reject(error)
    },
  )
}

import { enqueueMonitorEvent, getMonitorConfig } from '../client'

let installed = false

function shouldSkip(url) {
  const config = getMonitorConfig()
  return config.ignoreUrls?.some((item) => String(url || '').includes(item))
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
    (response) => {
      const startedAt = response.config?.metadata?.monitorStartedAt
      if (startedAt != null && !shouldSkip(response.config?.url)) {
        enqueueMonitorEvent({
          type: 'custom',
          level: response.status >= 400 ? 'warning' : 'info',
          name: 'api_request',
          trace_id: response.headers?.['x-trace-id'] || '',
          payload: {
            method: response.config?.method,
            url: response.config?.url,
            status: response.status,
            duration_ms: Math.round(performance.now() - startedAt),
            params: response.config?.params,
          },
        })
      }
      return response
    },
    (error) => {
      const config = error?.config || {}
      const startedAt = config.metadata?.monitorStartedAt
      if (startedAt != null && !shouldSkip(config.url)) {
        enqueueMonitorEvent({
          type: 'api_error',
          level: 'error',
          name: 'api_error',
          message: error.message || '接口请求异常',
          trace_id: error.response?.headers?.['x-trace-id'] || '',
          payload: {
            method: config.method,
            url: config.url,
            status: error.response?.status,
            code: error.response?.data?.code,
            duration_ms: Math.round(performance.now() - startedAt),
            params: config.params,
            request: config.data,
            response: error.response?.data,
          },
        })
      }
      return Promise.reject(error)
    },
  )
}

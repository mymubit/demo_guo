import { enqueueMonitorEvent, flushMonitorQueue, initMonitorClient, setMonitorUser } from './client'
import { installErrorCollector } from './collectors/error'
import { installPerformanceCollector } from './collectors/performance'
import { normalizeError } from './sanitize'

export { MonitorRouteTracker } from './collectors/router'
export { installAxiosMonitor } from './collectors/request'
export { flushMonitorQueue, setMonitorUser }

let initialized = false

export function initMonitor(options = {}) {
  const config = initMonitorClient(options)
  if (initialized) return config
  initialized = true
  installErrorCollector()
  installPerformanceCollector()
  return config
}

export function trackEvent(name, payload = {}, options = {}) {
  enqueueMonitorEvent({
    type: options.type || 'custom',
    level: options.level || 'info',
    name,
    message: options.message || '',
    route: options.route,
    payload,
  })
}

export function trackError(error, context = {}) {
  const normalized = normalizeError(error)
  enqueueMonitorEvent({
    type: context.type || 'js_error',
    level: context.level || 'error',
    name: context.name || normalized.error_type || 'manual_error',
    message: normalized.message || '手动上报错误',
    route: context.route,
    payload: { ...normalized, context },
  })
}

export function trackPageView(route, meta = {}) {
  enqueueMonitorEvent({
    type: 'page_view',
    level: 'info',
    name: 'page_view',
    route,
    payload: meta,
  })
}

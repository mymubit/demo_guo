import { enqueueMonitorEvent } from '../client'

let installed = false
const metrics = {}

function observeMetric(type, handler) {
  if (typeof PerformanceObserver === 'undefined') return
  try {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach(handler)
    })
    observer.observe({ type, buffered: true })
  } catch {
    // 部分浏览器不支持某些指标，忽略即可。
  }
}

export function installPerformanceCollector() {
  if (installed || typeof window === 'undefined') return
  installed = true

  observeMetric('paint', (entry) => {
    if (entry.name === 'first-paint') metrics.fp = Math.round(entry.startTime)
    if (entry.name === 'first-contentful-paint') metrics.fcp = Math.round(entry.startTime)
  })
  observeMetric('largest-contentful-paint', (entry) => {
    metrics.lcp = Math.round(entry.startTime)
  })
  observeMetric('layout-shift', (entry) => {
    if (!entry.hadRecentInput) metrics.cls = Number(((metrics.cls || 0) + entry.value).toFixed(4))
  })

  window.addEventListener('load', () => {
    window.setTimeout(() => {
      const nav = performance.getEntriesByType('navigation')?.[0]
      enqueueMonitorEvent({
        type: 'performance',
        level: 'info',
        name: 'web_vitals',
        performance: {
          ...metrics,
          dom_content_loaded: nav ? Math.round(nav.domContentLoadedEventEnd) : undefined,
          load: nav ? Math.round(nav.loadEventEnd) : undefined,
          ttfb: nav ? Math.round(nav.responseStart) : undefined,
          resource_count: performance.getEntriesByType('resource')?.length || 0,
        },
      })
    }, 0)
  })
}

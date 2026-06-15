import { enqueueMonitorEvent } from '../client'
import { normalizeError } from '../sanitize'

let installed = false

export function installErrorCollector() {
  if (installed || typeof window === 'undefined') return
  installed = true

  window.addEventListener(
    'error',
    (event) => {
      const target = event.target
      if (target && target !== window) {
        enqueueMonitorEvent({
          type: 'resource_error',
          level: 'error',
          message: `资源加载失败：${target.src || target.href || target.currentSrc || 'unknown'}`,
          payload: {
            tag_name: target.tagName,
            url: target.src || target.href || target.currentSrc,
          },
        })
        return
      }
      enqueueMonitorEvent({
        type: 'js_error',
        level: 'error',
        message: event.message || 'JS 运行错误',
        payload: {
          ...normalizeError(event.error),
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      })
    },
    true,
  )

  window.addEventListener('unhandledrejection', (event) => {
    enqueueMonitorEvent({
      type: 'promise_error',
      level: 'error',
      message: event.reason?.message || String(event.reason || 'Promise 未捕获异常'),
      payload: normalizeError(event.reason),
    })
  })
}

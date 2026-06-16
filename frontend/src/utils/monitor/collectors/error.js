import { enqueueMonitorEvent, getMonitorConfig } from '../client'
import { normalizeError } from '../sanitize'

let installed = false
let consoleInstalled = false

function stringifyConsoleArg(arg) {
  if (arg instanceof Error) return arg.message
  if (typeof arg === 'string') return arg
  try {
    return JSON.stringify(arg)
  } catch {
    return String(arg)
  }
}

function installConsoleCollector() {
  if (consoleInstalled || typeof window === 'undefined' || typeof console === 'undefined') return
  const config = getMonitorConfig()
  if (!config.captureConsole) return
  consoleInstalled = true
  const levels = config.consoleLevels || ['error', 'warn']
  levels.forEach((level) => {
    const original = console[level]
    if (typeof original !== 'function') return
    console[level] = (...args) => {
      original.apply(console, args)
      const message = args.map(stringifyConsoleArg).filter(Boolean).join(' ')
      if (!message) return
      enqueueMonitorEvent({
        type: level === 'error' ? 'js_error' : 'custom',
        level: level === 'error' ? 'error' : 'warning',
        name: `console.${level}`,
        message: message.slice(0, 1000),
        payload: {
          console_level: level,
          args: args.map(stringifyConsoleArg).slice(0, 5),
        },
      })
    }
  })
}

export function installErrorCollector() {
  if (installed || typeof window === 'undefined') return
  installed = true
  installConsoleCollector()

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

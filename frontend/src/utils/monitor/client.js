import { buildDefaultMonitorConfig } from './config'
import { clearCachedEvents, getSessionId, readCachedEvents, writeCachedEvents } from './storage'
import { payloadSize, sanitizePayload } from './sanitize'

let config = buildDefaultMonitorConfig()
let queue = []
let flushTimer = null
let currentUser = null
let isFlushing = false
let initialized = false

function shouldIgnore(event) {
  const message = event?.message || event?.payload?.message || ''
  const url = event?.page_url || event?.payload?.url || ''
  return (
    config.ignoreErrors?.some((item) => message.includes(item)) ||
    config.ignoreUrls?.some((item) => String(url).includes(item))
  )
}

function shouldSample() {
  const sampleRate = Math.max(0, Math.min(1, Number(config.sampleRate ?? 1)))
  return sampleRate >= 1 || Math.random() <= sampleRate
}

function normalizeEvent(event) {
  const payload = sanitizePayload(event.payload || {})
  const performance = sanitizePayload(event.performance || {})
  const normalized = {
    type: event.type || 'custom',
    level: event.level || 'info',
    name: event.name || '',
    message: event.message || '',
    page_url: event.page_url || window.location.href,
    route: event.route || window.location.pathname,
    browser: navigator.userAgent,
    os: navigator.platform || '',
    user_id: currentUser?.id || currentUser?.user_id || event.user_id || null,
    session_id: getSessionId(),
    trace_id: event.trace_id || '',
    payload,
    performance,
    timestamp: new Date().toISOString(),
  }
  if (payloadSize(normalized.payload) > config.maxPayloadSize) {
    normalized.payload = { truncated: true, reason: 'payload_too_large' }
  }
  return normalized
}

function scheduleFlush() {
  if (flushTimer) return
  flushTimer = window.setTimeout(() => {
    flushTimer = null
    flushMonitorQueue()
  }, config.flushInterval)
}

async function postEvents(events, useBeacon = false) {
  const body = JSON.stringify({ events })
  if (useBeacon && navigator.sendBeacon) {
    return navigator.sendBeacon(config.reportUrl, new Blob([body], { type: 'application/json' }))
  }
  const response = await fetch(config.reportUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: useBeacon,
  })
  return response.ok
}

export function configureMonitor(overrides = {}) {
  config = buildDefaultMonitorConfig({ ...config, ...overrides })
  return config
}

export function getMonitorConfig() {
  return config
}

export function setMonitorUser(user) {
  currentUser = user || null
}

export function enqueueMonitorEvent(event) {
  if (!config.enabled && !config.debug) return
  const normalized = normalizeEvent(event)
  if (shouldIgnore(normalized) || !shouldSample()) return
  const nextEvent = typeof config.beforeSend === 'function' ? config.beforeSend(normalized) : normalized
  if (!nextEvent) return
  if (config.debug && !config.enabled) {
    console.debug('[monitor]', nextEvent)
    return
  }
  queue.push(nextEvent)
  if (queue.length > config.maxQueueSize) queue = queue.slice(-config.maxQueueSize)
  if (queue.length >= config.batchSize) {
    flushMonitorQueue()
  } else {
    scheduleFlush()
  }
}

export async function flushMonitorQueue({ beacon = false } = {}) {
  if (isFlushing || (!queue.length && !readCachedEvents().length)) return
  isFlushing = true
  const cached = readCachedEvents()
  const batch = [...cached, ...queue].slice(0, config.batchSize)
  queue = queue.slice(Math.max(0, config.batchSize - cached.length))
  try {
    const ok = await postEvents(batch, beacon)
    if (ok) {
      clearCachedEvents()
    } else {
      writeCachedEvents(batch)
    }
  } catch {
    writeCachedEvents([...batch, ...queue].slice(-config.maxQueueSize))
  } finally {
    isFlushing = false
    if (queue.length) scheduleFlush()
  }
}

export function initMonitorClient(overrides = {}) {
  if (initialized) return config
  initialized = true
  configureMonitor(overrides)
  const cached = readCachedEvents()
  if (cached.length) queue = cached.slice(-config.maxQueueSize)
  window.addEventListener('online', () => flushMonitorQueue())
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flushMonitorQueue({ beacon: true })
  })
  window.addEventListener('beforeunload', () => flushMonitorQueue({ beacon: true }))
  scheduleFlush()
  return config
}

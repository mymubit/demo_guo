import { MONITOR_SESSION_KEY, MONITOR_STORAGE_KEY } from './config'

export function getSessionId() {
  try {
    let sessionId = sessionStorage.getItem(MONITOR_SESSION_KEY)
    if (!sessionId) {
      sessionId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`
      sessionStorage.setItem(MONITOR_SESSION_KEY, sessionId)
    }
    return sessionId
  } catch {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }
}

export function readCachedEvents() {
  try {
    const raw = localStorage.getItem(MONITOR_STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function writeCachedEvents(events) {
  try {
    localStorage.setItem(MONITOR_STORAGE_KEY, JSON.stringify(events || []))
  } catch {
    // localStorage 满或不可用时忽略，监控不能影响业务。
  }
}

export function clearCachedEvents() {
  try {
    localStorage.removeItem(MONITOR_STORAGE_KEY)
  } catch {
    // ignore
  }
}

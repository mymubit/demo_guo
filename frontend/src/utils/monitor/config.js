const DEFAULT_IGNORE_ERRORS = ['ResizeObserver loop limit exceeded', 'Network Error']
const DEFAULT_IGNORE_URLS = ['/api/monitoring/events/']
const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'http://localhost:8000'

export function resolveMonitorSampleRate(configValue, envFallback) {
  const envRate = Number(envFallback ?? import.meta.env.VITE_MONITORING_SAMPLE_RATE ?? 1)
  if (configValue === undefined || configValue === null || configValue === '') {
    return Math.max(0, Math.min(1, envRate))
  }
  const parsed = Number(configValue)
  if (!Number.isFinite(parsed)) {
    return Math.max(0, Math.min(1, envRate))
  }
  return Math.max(0, Math.min(1, parsed))
}

export const MONITOR_STORAGE_KEY = 'scriptforge-monitor-queue'
export const MONITOR_SESSION_KEY = 'scriptforge-monitor-session'

export function buildDefaultMonitorConfig(overrides = {}) {
  const env = import.meta.env.MODE || 'development'
  const enabledFromEnv = String(import.meta.env.VITE_MONITORING_ENABLED || '').toLowerCase()
  const enabled = enabledFromEnv ? ['1', 'true', 'yes'].includes(enabledFromEnv) : env === 'production'
  return {
    app: 'scriptforge-frontend',
    env,
    release: import.meta.env.VITE_APP_VERSION || '',
    enabled,
    debug: env !== 'production',
    sampleRate: resolveMonitorSampleRate(overrides.sampleRate),
    reportUrl: `${API_BASE_URL}/api/monitoring/events/`,
    batchSize: Number(import.meta.env.VITE_MONITORING_BATCH_SIZE || 10),
    maxQueueSize: Number(import.meta.env.VITE_MONITORING_MAX_QUEUE_SIZE || 200),
    flushInterval: Number(import.meta.env.VITE_MONITORING_FLUSH_INTERVAL || 10000),
    maxPayloadSize: Number(import.meta.env.VITE_MONITORING_MAX_PAYLOAD_SIZE || 16 * 1024),
    ignoreErrors: DEFAULT_IGNORE_ERRORS,
    ignoreUrls: DEFAULT_IGNORE_URLS,
    beforeSend: null,
    ...overrides,
  }
}

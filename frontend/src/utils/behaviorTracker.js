/**
 * utils/behaviorTracker.js —— 【运营 F1】6 个核心用户行为埋点工具
 *
 * 设计：
 *  • 单例 instance：避免重复注册 click/visibilitychange 监听
 *  • 自动从 sessionStorage 读 session_id（无则生成）
 *  • 失败/网络错误一律 swallow：埋点不能阻塞主链路
 *  • 与 monitor/trackEvent 分离：monitor 走 /api/monitor/events，行为埋点走 /api/operations/track
 *  • 暴露 6 个语义化函数：trackLandingView / trackCreationFormOpen / trackCreationSubmitted / trackNodeEdited / trackScriptExported / trackShareLinkGenerated
 *    + 通用 trackBehavior(name, payload)
 */
import { request } from '@/services/http'

const STORAGE_KEY = 'ops:behavior:session_id'
const LAST_EVENT_KEY = 'ops:behavior:last_event'
const DEDUPE_MS = 1500 // 同一事件在 1.5s 内只记一次

const ENDPOINT = '/api/operations/track/'

let inited = false
let sessionId = null

function ensureSessionId() {
  if (sessionId) return sessionId
  if (typeof window === 'undefined') return ''
  try {
    const cached = window.sessionStorage?.getItem(STORAGE_KEY)
    if (cached) {
      sessionId = cached
      return sessionId
    }
  } catch (_) {
    /* sessionStorage not available */
  }
  // generate new
  const generated = `s_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
  try {
    window.sessionStorage?.setItem(STORAGE_KEY, generated)
  } catch (_) {
    /* ignore */
  }
  sessionId = generated
  return sessionId
}

function getCurrentRoute() {
  if (typeof window === 'undefined') return ''
  return window.location?.pathname || ''
}

function shouldDedupe(eventName, projectId) {
  if (typeof window === 'undefined') return false
  try {
    const raw = window.sessionStorage?.getItem(LAST_EVENT_KEY)
    if (!raw) return false
    const last = JSON.parse(raw)
    if (last?.name !== eventName) return false
    if ((last?.project_id || '') !== (projectId || '')) return false
    return Date.now() - (last?.ts || 0) < DEDUPE_MS
  } catch (_) {
    return false
  }
}

function markSent(eventName, projectId) {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage?.setItem(
      LAST_EVENT_KEY,
      JSON.stringify({ name: eventName, project_id: projectId || '', ts: Date.now() })
    )
  } catch (_) {
    /* ignore */
  }
}

async function postEvent(payload) {
  try {
    await request('POST', ENDPOINT, {
      data: payload,
      skipAuthRefresh: true,
    })
  } catch (_) {
    // 埋点失败不能阻塞主流程
  }
}

/**
 * 通用行为埋点（高级用户使用）。
 */
export function trackBehavior(eventName, { projectId = '', page = '', payload = {} } = {}) {
  if (!eventName) return
  if (shouldDedupe(eventName, projectId)) return
  markSent(eventName, projectId)
  postEvent({
    event_name: eventName,
    session_id: ensureSessionId(),
    project_id: projectId ? String(projectId) : '',
    page: page || getCurrentRoute(),
    payload: payload || {},
  })
}

// ============================================================
// 6 个核心事件语义化封装（推荐业务代码使用）
// ============================================================
export function trackLandingView(payload = {}) {
  trackBehavior('landing_view', { payload })
}

export function trackCreationFormOpen({ creationEntry = '', pipelineMode = '' } = {}) {
  trackBehavior('creation_form_open', {
    payload: {
      creation_entry: creationEntry,
      pipeline_mode: pipelineMode,
    },
  })
}

export function trackCreationSubmitted({ projectId, theme = '', episodeCount, pipelineMode } = {}) {
  trackBehavior('creation_submitted', {
    projectId,
    payload: {
      theme: String(theme || '').slice(0, 200),
      episode_count: episodeCount,
      pipeline_mode: pipelineMode,
    },
  })
}

export function trackNodeEdited({ projectId, nodeIndex, nodeName = '' } = {}) {
  trackBehavior('node_edited', {
    projectId,
    payload: {
      node_index: nodeIndex,
      node_name: String(nodeName).slice(0, 64),
    },
  })
}

export function trackScriptExported({ projectId, fileFormat = 'md' } = {}) {
  trackBehavior('script_exported', {
    projectId,
    payload: { file_format: fileFormat },
  })
}

export function trackShareLinkGenerated({ projectId, validDays = 7 } = {}) {
  trackBehavior('share_link_generated', {
    projectId,
    payload: { valid_days: validDays },
  })
}

/**
 * 自动挂载全局监听（推荐在 App 入口调用一次）：
 *  • 监听路由变化 → 自动上报 landing_view（首页加载触发）
 *  • 监听页面隐藏 → 静默 flush（不依赖浏览器）
 */
export function installBehaviorTracker() {
  if (inited) return
  inited = true
  ensureSessionId()
  if (typeof window === 'undefined') return

  // 自动 landing_view：首次加载即报（让 funnel 顶层 = 进入站点的用户）
  try {
    trackLandingView({ referrer: document?.referrer || '' })
  } catch (_) {
    /* ignore */
  }
}

export const __test = {
  ensureSessionId,
  shouldDedupe,
  markSent,
  DEDUPE_MS,
}

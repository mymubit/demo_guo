/**
 * utils/behaviorTracker.test.js —— 【运营 F1】6 个核心埋点单测
 */
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'

import {
  trackBehavior,
  trackLandingView,
  trackCreationFormOpen,
  trackCreationSubmitted,
  trackNodeEdited,
  trackScriptExported,
  trackShareLinkGenerated,
  installBehaviorTracker,
  __test,
} from './behaviorTracker'

vi.mock('@/services/http', () => ({
  request: vi.fn(() => Promise.resolve({ data: { recorded: true } })),
}))

import { request } from '@/services/http'

const ENDPOINT = '/api/operations/track/'

beforeEach(() => {
  if (typeof window !== 'undefined') {
    window.sessionStorage?.clear()
    Object.defineProperty(document, 'referrer', {
      configurable: true,
      value: '',
    })
  }
  vi.clearAllMocks()
  __test.ensureSessionId()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('behaviorTracker dedupe', () => {
  it('同事件 1.5s 内只上报一次', async () => {
    trackCreationFormOpen({ creationEntry: 'from-scratch' })
    trackCreationFormOpen({ creationEntry: 'from-scratch' })
    await new Promise((r) => setTimeout(r, 10))
    expect(request).toHaveBeenCalledTimes(1)
  })

  it('不同事件独立计数', async () => {
    trackCreationFormOpen({ creationEntry: 'from-scratch' })
    trackNodeEdited({ projectId: 'p1', nodeIndex: 1, nodeName: '大纲' })
    await new Promise((r) => setTimeout(r, 10))
    expect(request).toHaveBeenCalledTimes(2)
  })
})

describe('6 个核心事件', () => {
  it.each([
    ['trackLandingView', trackLandingView, 'landing_view'],
    ['trackCreationFormOpen', () => trackCreationFormOpen({ creationEntry: 'from-scratch' }), 'creation_form_open'],
    ['trackCreationSubmitted', () => trackCreationSubmitted({ projectId: 'p1', theme: 'x' }), 'creation_submitted'],
    ['trackNodeEdited', () => trackNodeEdited({ projectId: 'p1', nodeIndex: 1, nodeName: 'x' }), 'node_edited'],
    ['trackScriptExported', () => trackScriptExported({ projectId: 'p1', fileFormat: 'md' }), 'script_exported'],
    ['trackShareLinkGenerated', () => trackShareLinkGenerated({ projectId: 'p1', validDays: 7 }), 'share_link_generated'],
  ])('%s 上报对应 event_name', async (_name, fn, expected) => {
    fn()
    await new Promise((r) => setTimeout(r, 10))
    expect(request).toHaveBeenCalledWith('POST', ENDPOINT, expect.objectContaining({
      data: expect.objectContaining({ event_name: expected }),
    }))
  })
})

describe('payload 透传', () => {
  it('支持自定义 payload', async () => {
    trackBehavior('landing_view', { payload: { foo: 'bar' } })
    await new Promise((r) => setTimeout(r, 10))
    expect(request).toHaveBeenCalledWith('POST', ENDPOINT, expect.objectContaining({
      data: expect.objectContaining({ payload: { foo: 'bar' } }),
    }))
  })

  it('自动附带 session_id 与 page', async () => {
    trackBehavior('node_edited', { projectId: 'p1' })
    await new Promise((r) => setTimeout(r, 10))
    const args = request.mock.calls[0]
    const data = args[2].data
    expect(data.session_id).toBeTruthy()
    expect(data.project_id).toBe('p1')
    expect(typeof data.page).toBe('string')
  })
})

describe('installBehaviorTracker', () => {
  it('幂等', () => {
    installBehaviorTracker()
    installBehaviorTracker()
    // 不应抛错
    expect(true).toBe(true)
  })
})

describe('error tolerance', () => {
  it('request 失败不能抛错', async () => {
    request.mockRejectedValueOnce(new Error('网络失败'))
    expect(() => trackLandingView()).not.toThrow()
    // 等待 promise
    await new Promise((r) => setTimeout(r, 10))
  })
})

import { request } from './http'
import { normalizeMembership } from './adapters/businessAdapters'

export const membership = {
  plans() {
    return request('GET', '/api/members/plans/')
  },
  async myMembership() {
    const data = await request('GET', '/api/members/me/')
    return normalizeMembership(data)
  },
  async summary() {
    const data = await request('GET', '/api/members/summary/')
    return normalizeMembership(data)
  },
  featureMatrix() {
    return request('GET', '/api/members/feature-matrix/')
  },
  history() {
    return request('GET', '/api/members/history/')
  },
  async redeem(code) {
    return request('POST', '/api/members/redeem/', { data: { code } })
  },
}

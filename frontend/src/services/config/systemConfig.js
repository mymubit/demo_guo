import { request } from '../http'

export const systemConfig = {
  publicAll() {
    return request('GET', '/api/system-configs/public/')
  },
  batch(keys = []) {
    return request('POST', '/api/system-configs/batch/', { data: { keys } })
  },
  detail(key) {
    return request('GET', `/api/system-configs/${encodeURIComponent(key)}/`)
  },
}

export default systemConfig

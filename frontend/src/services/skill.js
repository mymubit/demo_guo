import { request } from './http'

export const skill = {
  themes() {
    return request('GET', '/api/skill/themes/public/')
  },
}

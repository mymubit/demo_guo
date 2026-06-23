import { request } from './http'
import { normalizeWorkDetail, normalizeWorkItem } from './adapters/businessAdapters'
import { normalizeListResult } from './adapters/listAdapter'
import { UI_WORK_STATUS_TO_API_STATUS } from './constants/businessEnums'

export const works = {
  async list(page, status, pageSize = 12, options = {}) {
    const apiStatus = UI_WORK_STATUS_TO_API_STATUS[status] ?? status
    const data = await request('GET', '/api/works/', {
      params: {
        page: page || 1,
        page_size: pageSize,
        status: apiStatus && apiStatus !== 'all' ? apiStatus : undefined,
        q: options.q || undefined,
        ordering: options.ordering || undefined,
      },
    })
    const result = normalizeListResult(data, normalizeWorkItem)
    return { items: result.items, pagination: result.pagination }
  },
  async detail(projectId) {
    const data = await request('GET', `/api/works/${projectId}/`)
    return normalizeWorkDetail(data)
  },
  remove(projectId) {
    return request('DELETE', `/api/works/${projectId}/`)
  },
  share(projectId, options) {
    return request('POST', `/api/works/${projectId}/share/`, { data: options || {} })
  },
  exportMarkdown(projectId) {
    return request('GET', `/api/works/${projectId}/export/`, { params: { format: 'md' } })
  },
  stats() {
    return request('GET', '/api/works/stats/')
  },
  applyPolish(projectId, options = {}) {
    return request('POST', `/api/works/${projectId}/agents/drama.polish-master/apply/`, { data: options })
  },
}

/** 后台创作项目详情页路径（统一入口） */
export function adminProjectDetailPath(projectId, tab = 'basic') {
  const id = String(projectId || '').trim()
  if (!id) return '/admin/creation/projects'
  const params = new URLSearchParams()
  if (tab && tab !== 'basic') params.set('tab', tab)
  const qs = params.toString()
  return `/admin/creation/projects/${id}${qs ? `?${qs}` : ''}`
}

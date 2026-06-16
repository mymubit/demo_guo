import { Navigate, useSearchParams } from 'react-router-dom'

/** 兼容旧入口：/admin/orchestration?view=stats → Hub monitor Tab */
export default function OrchestrationMonitor() {
  const [searchParams] = useSearchParams()
  const view = searchParams.get('view')
  const tab = searchParams.get('tab') || 'monitor'
  const params = new URLSearchParams()
  params.set('tab', tab === 'flow' ? 'flow' : 'monitor')
  if (view) params.set('view', view)
  return <Navigate to={`/admin/orchestration?${params.toString()}`} replace />
}

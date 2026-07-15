import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Settings2 } from 'lucide-react'
import { PipelineRail } from '@/components/workbench/PipelineRail'
import { ModulePanel } from '@/components/workbench/ModulePanel'
import { StageCanvas } from '@/components/workbench/StageCanvas'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { workbenchStages } from '@/utils/pipeline'
import type { StageDefinition } from '@/types/workbench'

const WORKFLOW_STATUS_LABELS = {
  active: '进行中',
  waiting_approval: '待审批',
  waiting_quality: '质检中',
  waiting_user: '待决策',
  completed: '已完成',
  blocked: '已阻塞',
} as const

export function WorkbenchPage() {
  const { projectId = '' } = useParams()

  const settingsQuery = useQuery({
    queryKey: ['settings', projectId],
    queryFn: () => dramaApi.getSettings(projectId),
    enabled: Boolean(projectId),
  })

  const workflowQuery = useQuery({
    queryKey: ['workflow', projectId],
    queryFn: () => dramaApi.getWorkflow(projectId),
    enabled: Boolean(projectId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'waiting_quality' || status === 'active' ? 5000 : false
    },
  })

  const stages = useMemo(() => {
    if (!settingsQuery.data) return []
    return workbenchStages({
      entry_type: settingsQuery.data.entry_type,
      enable_delivery: settingsQuery.data.creation_preferences.enable_delivery,
      creation_preferences: settingsQuery.data.creation_preferences,
    })
  }, [settingsQuery.data])

  const [activeStageId, setActiveStageId] = useState<string | null>(null)
  const activeStage: StageDefinition | null =
    stages.find((s) => s.id === (activeStageId ?? stages[0]?.id)) ?? null

  if (settingsQuery.isLoading || workflowQuery.isLoading) return <LoadingBlock label="加载工作台…" />

  if (settingsQuery.isError) {
    return (
      <div className="p-8">
        <ErrorBanner
          message={formatApiError(settingsQuery.error)}
          onRetry={() => void settingsQuery.refetch()}
        />
      </div>
    )
  }

  if (workflowQuery.isError) {
    return (
      <div className="p-8">
        <ErrorBanner
          message={formatApiError(workflowQuery.error)}
          onRetry={() => void workflowQuery.refetch()}
        />
      </div>
    )
  }

  if (!settingsQuery.data || !workflowQuery.data || !activeStage) {
    return <div className="p-8 text-sm text-ink-muted">工作台数据不完整</div>
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
        <div>
          <h1 className="text-base font-semibold text-ink">
            {settingsQuery.data.title || '创作工作台'}
          </h1>
          <p className="text-xs text-ink-muted">
            {settingsQuery.data.entry_type === 'original_track' ? '原创通道' : '改编通道'} ·{' '}
            {WORKFLOW_STATUS_LABELS[workflowQuery.data.status]}
          </p>
        </div>
        <Link to={`/projects/${projectId}/settings`}>
          <Button variant="secondary" size="sm" iconLeft={<Settings2 className="h-3.5 w-3.5" />}>
            项目设置
          </Button>
        </Link>
      </div>

      <div className="flex min-h-0 flex-1">
        <PipelineRail
          settings={settingsQuery.data}
          workflow={workflowQuery.data}
          activeStageId={activeStage.id}
          onSelect={(stage) => setActiveStageId(stage.id)}
        />
        <StageCanvas
          projectId={projectId}
          stage={activeStage}
          settings={settingsQuery.data}
          workflow={workflowQuery.data}
        />
        <ModulePanel stage={activeStage} settings={settingsQuery.data} />
      </div>
    </div>
  )
}

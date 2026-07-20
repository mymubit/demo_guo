import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { PanelRightOpen, Settings2 } from 'lucide-react'
import { PipelineRail } from '@/components/workbench/PipelineRail'
import { ModulePanel } from '@/components/workbench/ModulePanel'
import { StageCanvas } from '@/components/workbench/StageCanvas'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import {
  isGenreMatrixComplete,
  isWorkflowFirstRun,
  resolveFirstRunStageId,
} from '@/utils/firstRunGuide'
import { rememberRecentProject } from '@/utils/recentProjects'
import { workbenchStages } from '@/utils/pipeline'
import type { StageDefinition } from '@/types/workbench'
import { useCompactPcLayout } from '@/hooks/useDesktopLayout'

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
  const [searchParams, setSearchParams] = useSearchParams()
  const forceGuide = searchParams.get('guide') === '1'
  const { definition } = useWorkbenchDefinition()

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
    return workbenchStages(definition, {
      entry_type: settingsQuery.data.entry_type,
      enable_delivery: settingsQuery.data.creation_preferences.enable_delivery,
      creation_preferences: settingsQuery.data.creation_preferences,
    })
  }, [definition, settingsQuery.data])

  const [activeStageId, setActiveStageId] = useState<string | null>(null)
  const [guidePinned, setGuidePinned] = useState(forceGuide)
  const isCompactPc = useCompactPcLayout()
  const [isModulePanelOpen, setIsModulePanelOpen] = useState(true)

  useEffect(() => {
    setIsModulePanelOpen(!isCompactPc)
  }, [isCompactPc])

  useEffect(() => {
    if (!settingsQuery.data || !projectId) return
    rememberRecentProject({
      id: projectId,
      title: settingsQuery.data.title,
      entry_type: settingsQuery.data.entry_type,
    })
  }, [projectId, settingsQuery.data])

  // 首跑或带 guide=1：自动聚焦可执行主链阶段（通常是立项简报）
  useEffect(() => {
    if (!workflowQuery.data || stages.length === 0) return
    if (activeStageId) return
    const shouldAutoFocus = forceGuide || isWorkflowFirstRun(workflowQuery.data)
    if (!shouldAutoFocus) return
    const targetId = resolveFirstRunStageId(stages, workflowQuery.data)
    if (targetId) setActiveStageId(targetId)
  }, [stages, workflowQuery.data, activeStageId, forceGuide])

  useEffect(() => {
    if (forceGuide) setGuidePinned(true)
  }, [forceGuide])

  const dismissGuide = () => {
    setGuidePinned(false)
    if (searchParams.has('guide')) {
      const next = new URLSearchParams(searchParams)
      next.delete('guide')
      setSearchParams(next, { replace: true })
    }
  }

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

  const themeReady = isGenreMatrixComplete(settingsQuery.data.genre_matrix)
  const firstRun = isWorkflowFirstRun(workflowQuery.data)

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas">
      {/* 影棚紧凑顶栏：与下方冷雾画布拉开密度差 */}
      <div className="flex h-11 shrink-0 items-center justify-between gap-3 border-b border-white/10 bg-shell px-3 text-shell-ink">
        <div className="flex min-w-0 items-center gap-3">
          <span className="hidden h-5 w-0.5 shrink-0 rounded-full bg-shell-accent sm:block" />
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold tracking-wide text-white">
              {settingsQuery.data.title || '创作工作台'}
            </h1>
            <p className="truncate text-[11px] text-shell-muted">
              {settingsQuery.data.entry_type === 'original_track' ? '原创通道' : '改编通道'}
              <span className="mx-1.5 text-white/20">·</span>
              <span className="text-shell-accent">
                {WORKFLOW_STATUS_LABELS[workflowQuery.data.status]}
              </span>
              {firstRun ? <span className="text-shell-muted"> · 首跑</span> : null}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {isCompactPc ? (
            <Button
              variant="ghost"
              size="sm"
              className="text-shell-muted hover:bg-white/10 hover:text-white"
              iconLeft={<PanelRightOpen className="h-3.5 w-3.5" />}
              aria-expanded={isModulePanelOpen}
              onClick={() => setIsModulePanelOpen((value) => !value)}
            >
              能力模块
            </Button>
          ) : null}
          <Link to={`/projects/${projectId}/settings`}>
            <Button
              variant="ghost"
              size="sm"
              className="text-shell-muted hover:bg-white/10 hover:text-white"
              iconLeft={<Settings2 className="h-3.5 w-3.5" />}
            >
              创作设定
            </Button>
          </Link>
        </div>
      </div>

      {!themeReady ? (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-xs text-amber-900">
          题材未选齐，建议先完善创作设定再执行主链。
          <Link
            className="ml-2 font-medium text-action underline underline-offset-2"
            to={`/projects/${projectId}/settings?focus=theme`}
          >
            去选题材
          </Link>
        </div>
      ) : null}

      <div className="relative flex min-h-0 flex-1">
        <PipelineRail
          settings={settingsQuery.data}
          workflow={workflowQuery.data}
          activeStageId={activeStage.id}
          onSelect={(stage) => {
            setActiveStageId(stage.id)
            dismissGuide()
          }}
        />
        <StageCanvas
          projectId={projectId}
          stage={activeStage}
          settings={settingsQuery.data}
          workflow={workflowQuery.data}
          forceFirstRunGuide={guidePinned}
          onDismissFirstRunGuide={dismissGuide}
        />
        {!isCompactPc ? (
          <ModulePanel stage={activeStage} settings={settingsQuery.data} />
        ) : isModulePanelOpen ? (
          <>
            <button
              type="button"
              aria-label="关闭能力模块遮罩"
              className="absolute inset-0 z-20 bg-slate-950/10"
              onClick={() => setIsModulePanelOpen(false)}
            />
            <ModulePanel
              stage={activeStage}
              settings={settingsQuery.data}
              className="absolute inset-y-0 right-0 z-30 w-[300px] shadow-panel"
              onClose={() => setIsModulePanelOpen(false)}
            />
          </>
        ) : null}
      </div>
    </div>
  )
}

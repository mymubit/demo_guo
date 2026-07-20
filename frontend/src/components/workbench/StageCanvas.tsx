import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { FilterEmptyState } from '@/components/layout/FilterEmptyState'
import { PageSection } from '@/components/layout/PageSection'
import {
  EpisodeScriptsView,
  NarrativePlanView,
  ProjectBriefView,
  ReportArtifactView,
} from '@/components/artifacts/ArtifactViews'
import { StoryBibleView } from '@/components/artifacts/StoryBibleView'
import { DeliveryTabs } from '@/components/artifacts/DeliveryTabs'
import { QualityLoopPanel } from '@/components/workbench/QualityLoopPanel'
import { GenerationJobPanel } from '@/components/workbench/GenerationJobPanel'
import { GenerationTroubleCard } from '@/components/workbench/GenerationTroubleCard'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { isThemeRequirementMet, shouldShowFirstRunExecuteGuide } from '@/utils/firstRunGuide'
import { canExecuteStage, explainExecuteGate } from '@/utils/pipeline'
import { createCommandId } from '@/utils/cn'
import type { DeliveryItem, GenerationJob, ProjectSettings, WorkflowState } from '@/types/domain'
import type { StageDefinition } from '@/types/workbench'
import { useEffect, useState } from 'react'

const STRUCTURED_ARTIFACTS = new Set([
  'project_brief',
  'story_bible',
  'narrative_plan',
  'episode_scripts',
  'production_package',
  'quality_report',
  'compliance_report',
  'polished_script',
])

export function StageCanvas({
  projectId,
  stage,
  settings,
  workflow,
  forceFirstRunGuide = false,
  onDismissFirstRunGuide,
}: {
  projectId: string
  stage: StageDefinition
  settings: ProjectSettings
  workflow: WorkflowState
  forceFirstRunGuide?: boolean
  onDismissFirstRunGuide?: () => void
}) {
  const qc = useQueryClient()
  const [sessionJob, setSessionJob] = useState<GenerationJob | null>(null)
  const artifactKey = stage.artifact === 'production_package' ? 'production_package' : stage.artifact
  const gateReason = explainExecuteGate(stage, workflow)
  const executable = gateReason === null && canExecuteStage(stage, workflow)

  useEffect(() => {
    setSessionJob(null)
  }, [stage.id])

  const latestJobQuery = useQuery({
    queryKey: ['generation-latest', projectId, stage.role, artifactKey],
    queryFn: () =>
      dramaApi.getLatestGeneration(projectId, {
        role: stage.role,
        artifact_key: artifactKey || undefined,
      }),
    enabled: Boolean(projectId && stage.role),
    retry: false,
  })

  const job = sessionJob ?? latestJobQuery.data ?? null

  const artifactQuery = useQuery({
    queryKey: ['artifact', projectId, artifactKey],
    queryFn: () => dramaApi.getArtifact<Record<string, unknown>>(projectId, artifactKey),
    enabled: Boolean(artifactKey),
    retry: false,
  })

  const qualityQuery = useQuery({
    queryKey: ['artifact', projectId, 'quality_report'],
    queryFn: () => dramaApi.getArtifact<Record<string, unknown>>(projectId, 'quality_report'),
    enabled:
      stage.stage_kind === 'quality_loop' ||
      workflow.current_phase === 'quality' ||
      workflow.status === 'waiting_user',
    retry: false,
  })

  const complianceQuery = useQuery({
    queryKey: ['artifact', projectId, 'compliance_report'],
    queryFn: () => dramaApi.getArtifact<Record<string, unknown>>(projectId, 'compliance_report'),
    enabled:
      stage.stage_kind === 'quality_loop' ||
      workflow.current_phase === 'quality' ||
      workflow.status === 'waiting_user',
    retry: false,
  })

  const refreshWorkbench = () => {
    void qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    void qc.invalidateQueries({ queryKey: ['artifact', projectId] })
    void qc.invalidateQueries({ queryKey: ['generation-latest', projectId] })
    void qc.invalidateQueries({ queryKey: ['job-llm-logs'] })
  }

  const runMutation = useMutation({
    mutationFn: async () => {
      const input =
        stage.id === 'writing'
          ? {
              episode_range: {
                start: workflow.batch_cursor,
                count: settings.creation_preferences.batch_episode_max,
              },
            }
          : {}
      return dramaApi.startGeneration(projectId, {
        command_id: createCommandId(`run-${stage.id}`),
        expected_version: workflow.version,
        role: stage.role,
        input,
      })
    },
    onSuccess: (started) => {
      setSessionJob(started)
    },
  })

  const approvalMutation = useMutation({
    mutationFn: (decision: 'approve' | 'reject') =>
      dramaApi.approveStoryBible(projectId, {
        command_id: createCommandId('approval'),
        decision,
        expected_version: workflow.version,
      }),
    onSuccess: () => {
      refreshWorkbench()
    },
  })

  const showQuality =
    stage.stage_kind === 'quality_loop' ||
    workflow.current_phase === 'quality' ||
    workflow.current_phase === 'revision' ||
    workflow.status === 'waiting_user' ||
    workflow.status === 'waiting_quality'

  const payload = artifactQuery.data?.payload ?? null
  const qualityPayload = (qualityQuery.data?.payload ?? null) as
    | {
        overall_score?: number
        grade?: string
        verdict?: string
        needs_revision?: boolean
        dimensions?: Record<string, { score?: number }>
      }
    | null
  const compliancePayload = (complianceQuery.data?.payload ?? null) as
    | {
        overall_result?: string
        blocking_issues?: unknown[]
        risk_items?: Array<{ type: string; description: string; suggestion: string }>
      }
    | null

  const themeIncomplete = !isThemeRequirementMet(settings)

  const showFirstRunGuide = shouldShowFirstRunExecuteGuide({
    settings,
    workflow,
    stage,
    hasPayload: payload != null,
    executable,
    forceGuide: forceFirstRunGuide,
  })

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-canvas">
      <header className="flex items-center justify-between border-b border-border/80 bg-surface/90 px-8 py-4">
        <PageSection
          eyebrow="阶段画布"
          title={stage.label_zh}
          description="当前由对应创作角色执行，完成后自动保存阶段产物"
          className="mb-0"
        />
        <Button
          variant="action"
          iconLeft={<Play className="h-4 w-4" />}
          loading={runMutation.isPending}
          disabled={!executable}
          aria-disabled={!executable}
          title={executable ? '执行本阶段' : gateReason ?? '当前不可执行'}
          onClick={() => {
            if (!executable) return
            onDismissFirstRunGuide?.()
            runMutation.mutate()
          }}
        >
          执行本阶段
        </Button>
      </header>

      <div className="w-full flex-1 space-y-6 overflow-auto px-[clamp(2rem,3.5vw,3.5rem)] py-[clamp(1.5rem,2.5vw,2.5rem)]">
        {themeIncomplete ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-medium">题材尚未满足，生成将被门禁拦截</p>
            <p className="mt-1">
              请先到{' '}
              <Link
                className="font-medium text-action underline underline-offset-2"
                to={`/projects/${projectId}/settings?focus=theme`}
              >
                创作设定
              </Link>{' '}
              完成题材四轴矩阵，或选择预设题材码后再执行。
            </p>
          </div>
        ) : null}

        {showFirstRunGuide ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-medium">下一步：生成「{stage.label_zh}」</p>
                <p className="mt-1 text-emerald-900/90">
                  题材已就绪。点击右上角「执行本阶段」，即可启动主链第一步。
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="action"
                  size="sm"
                  loading={runMutation.isPending}
                  disabled={!executable}
                  iconLeft={<Play className="h-3.5 w-3.5" />}
                  onClick={() => {
                    if (!executable) return
                    onDismissFirstRunGuide?.()
                    runMutation.mutate()
                  }}
                >
                  立即执行
                </Button>
                {onDismissFirstRunGuide ? (
                  <Button size="sm" variant="secondary" onClick={onDismissFirstRunGuide}>
                    知道了
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {!executable && gateReason ? (
          <div className="rounded-lg border border-border bg-surface px-4 py-3 text-sm text-ink">
            <p className="font-medium text-ink">当前无法执行本阶段</p>
            <p className="mt-1 text-ink-muted">{gateReason}</p>
          </div>
        ) : null}

        {runMutation.isError ? (
          <GenerationTroubleCard message={formatApiError(runMutation.error)} status="failed" />
        ) : null}
        {approvalMutation.isError ? <ErrorBanner message={formatApiError(approvalMutation.error)} /> : null}
        {artifactQuery.isError ? (
          <ErrorBanner
            message={formatApiError(artifactQuery.error)}
            onRetry={() => void artifactQuery.refetch()}
          />
        ) : null}

        {job ? (
          <GenerationJobPanel
            projectId={projectId}
            job={job}
            onJobUpdate={(latest) => {
              setSessionJob(latest)
            }}
            onCompleted={() => {
              refreshWorkbench()
            }}
          />
        ) : null}

        {showQuality ? (
          <QualityLoopPanel
            projectId={projectId}
            workflow={workflow}
            qualityReport={qualityPayload}
            complianceReport={compliancePayload}
          />
        ) : null}

        {artifactQuery.isLoading ? <LoadingBlock label="加载产物…" /> : null}

        {!artifactQuery.isLoading && !artifactQuery.isError && payload == null && stage.artifact !== 'production_package' ? (
          <FilterEmptyState
            title={`「${stage.label_zh}」暂无产物`}
            description={
              executable
                ? `点击右上角「执行本阶段」，生成「${stage.label_zh}」内容。`
                : gateReason ?? `完成前置阶段后，即可生成「${stage.label_zh}」。`
            }
            variant="inbox"
            className="min-h-[12rem]"
          />
        ) : null}

        {payload ? (
          <PageSection eyebrow="阶段产物" title={stage.label_zh}>
            <div className="space-y-4">
              {stage.artifact === 'project_brief' ? <ProjectBriefView data={payload} /> : null}

              {stage.artifact === 'story_bible' ? (
                <StoryBibleView
                  data={payload}
                  waitingApproval={
                    workflow.status === 'waiting_approval' ||
                    workflow.current_phase === 'blueprint_approval'
                  }
                  approvalPending={approvalMutation.isPending}
                  onApprove={() => approvalMutation.mutate('approve')}
                  onReject={() => approvalMutation.mutate('reject')}
                />
              ) : null}

              {stage.artifact === 'narrative_plan' ? <NarrativePlanView data={payload} /> : null}

              {stage.artifact === 'episode_scripts' ? <EpisodeScriptsView data={payload} /> : null}

              {stage.artifact === 'quality_report' ||
              stage.artifact === 'compliance_report' ||
              stage.artifact === 'polished_script' ? (
                <ReportArtifactView kind={stage.artifact} data={payload} />
              ) : null}

              {stage.artifact === 'production_package' ? (
                <DeliveryTabs
                  packageData={payload}
                  enabledItems={
                    (settings.creation_preferences.deliverables ?? []) as DeliveryItem[]
                  }
                />
              ) : null}

              {!STRUCTURED_ARTIFACTS.has(stage.artifact) ? (
                <ReportArtifactView kind="generic" data={payload} />
              ) : null}
            </div>
          </PageSection>
        ) : stage.artifact === 'production_package' ? (
          <DeliveryTabs
            packageData={payload}
            enabledItems={(settings.creation_preferences.deliverables ?? []) as DeliveryItem[]}
          />
        ) : null}
      </div>
    </div>
  )
}

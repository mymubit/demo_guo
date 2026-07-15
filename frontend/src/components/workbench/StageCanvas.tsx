import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import {
  EpisodeScriptsView,
  NarrativePlanView,
  ProjectBriefView,
  StoryBibleView,
} from '@/components/artifacts/ArtifactViews'
import { DeliveryTabs } from '@/components/artifacts/DeliveryTabs'
import { QualityLoopPanel } from '@/components/workbench/QualityLoopPanel'
import { GenerationJobPanel } from '@/components/workbench/GenerationJobPanel'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { canExecuteStage } from '@/utils/pipeline'
import { createCommandId } from '@/utils/cn'
import type { DeliveryItem, GenerationJob, ProjectSettings, WorkflowState } from '@/types/domain'
import type { StageDefinition } from '@/types/workbench'
import { useState } from 'react'

export function StageCanvas({
  projectId,
  stage,
  settings,
  workflow,
}: {
  projectId: string
  stage: StageDefinition
  settings: ProjectSettings
  workflow: WorkflowState
}) {
  const qc = useQueryClient()
  const [job, setJob] = useState<GenerationJob | null>(null)
  const artifactKey = stage.artifact === 'production_package' ? 'production_package' : stage.artifact
  const executable = canExecuteStage(stage, workflow)

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
      setJob(started)
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

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
        <div>
          <h2 className="text-base font-semibold text-ink">{stage.label_zh}</h2>
          <p className="text-xs text-ink-muted">
            产物 {stage.artifact} · 工作流 v{workflow.version} · 阶段 {workflow.current_phase}
          </p>
        </div>
        <Button
          iconLeft={<Play className="h-4 w-4" />}
          loading={runMutation.isPending}
          disabled={!executable}
          aria-disabled={!executable}
          title={executable ? '执行本阶段' : '当前阶段不可执行（门禁未通过或已锁定）'}
          onClick={() => {
            if (!executable) return
            runMutation.mutate()
          }}
        >
          执行本阶段
        </Button>
      </header>

      <div className="flex-1 space-y-4 overflow-auto p-5">
        {runMutation.isError ? <ErrorBanner message={formatApiError(runMutation.error)} /> : null}
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
          <EmptyState
            title="暂无产物"
            description={`阶段「${stage.label_zh}」尚未生成 ${stage.artifact}，请在门禁允许时点击「执行本阶段」。`}
          />
        ) : null}

        {payload && stage.artifact === 'project_brief' ? <ProjectBriefView data={payload} /> : null}

        {payload && stage.artifact === 'story_bible' ? (
          <StoryBibleView
            data={payload}
            waitingApproval={
              workflow.status === 'waiting_approval' || workflow.current_phase === 'blueprint_approval'
            }
            approvalPending={approvalMutation.isPending}
            onApprove={() => approvalMutation.mutate('approve')}
            onReject={() => approvalMutation.mutate('reject')}
          />
        ) : null}

        {payload && stage.artifact === 'narrative_plan' ? <NarrativePlanView data={payload} /> : null}

        {payload && stage.artifact === 'episode_scripts' ? <EpisodeScriptsView data={payload} /> : null}

        {stage.artifact === 'production_package' ? (
          <DeliveryTabs
            packageData={payload}
            enabledItems={(settings.creation_preferences.delivery_items ?? []) as DeliveryItem[]}
          />
        ) : null}

        {payload &&
        !['project_brief', 'story_bible', 'narrative_plan', 'episode_scripts', 'production_package'].includes(
          stage.artifact,
        ) ? (
          <pre className="sf-panel overflow-auto p-4 text-xs text-ink-muted">
            {JSON.stringify(payload, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  )
}

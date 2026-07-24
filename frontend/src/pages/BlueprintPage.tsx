import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { ArtifactPreview } from '@/components/ArtifactPreview'
import { Button } from '@/components/ui/Button'
import { Tabs } from '@/components/ui/Tabs'
import {
  isStageRunInProgress,
  StageStatusPanel,
} from '@/components/workflow/StageStatusPanel'
import { formatApiError } from '@/services/errors'
import {
  confirmBlueprint,
  generateBlueprint,
  getBlueprintState,
} from '@/services/v3/blueprint'
import { getTopicState } from '@/services/v3/topic'
import type { ArtifactVersion, BlueprintBundle } from '@/types/v3/domain'
import { resolveNextStageCta } from './projectLabels'

const BLUEPRINT_TABS = [
  { id: 'story_bible', label: '故事蓝图' },
  { id: 'character_system', label: '人物' },
  { id: 'world_system', label: '世界' },
  { id: 'emotion_system', label: '情绪' },
  { id: 'originality_report', label: '原创性' },
] as const

type BlueprintTabId = (typeof BLUEPRINT_TABS)[number]['id']

function readStringField(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key]
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function pickArtifact(
  bundle: BlueprintBundle | null | undefined,
  key: string,
): ArtifactVersion | null {
  if (!bundle) return null
  return bundle[key] ?? null
}

function ArtifactPanel({
  artifact,
  heading,
}: {
  artifact: ArtifactVersion
  heading: string
}) {
  const payload = artifact.payload ?? {}
  const title =
    readStringField(payload, 'title') ??
    readStringField(payload, 'name') ??
    readStringField(payload, 'summary')
  const premise =
    readStringField(payload, 'core_premise') ??
    readStringField(payload, 'logline') ??
    readStringField(payload, 'overview')

  return (
    <section className="sf-panel space-y-3 p-4">
      <h2 className="text-sm font-semibold text-ink">{heading}</h2>
      {title || premise ? (
        <dl className="grid gap-3 sm:grid-cols-2">
          {title ? (
            <div className="sm:col-span-2">
              <dt className="text-xs text-ink-faint">摘要</dt>
              <dd className="mt-1 text-sm text-ink">{title}</dd>
            </div>
          ) : null}
          {premise ? (
            <div className="sm:col-span-2">
              <dt className="text-xs text-ink-faint">要点</dt>
              <dd className="mt-1 text-sm text-ink">{premise}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
      <ArtifactPreview payload={payload} />
    </section>
  )
}

export function BlueprintPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<BlueprintTabId>('story_bible')

  const blueprintQuery = useQuery({
    queryKey: ['v3', 'blueprint', id],
    queryFn: () => getBlueprintState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const topicQuery = useQuery({
    queryKey: ['v3', 'topic', id],
    queryFn: () => getTopicState(id!),
    enabled: Boolean(id),
  })

  const blueprint = blueprintQuery.data
  const hasCommittedBrief = Boolean(topicQuery.data?.committed)

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'blueprint', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const generateMutation = useMutation({
    mutationFn: () => generateBlueprint(id!),
    onSuccess: invalidate,
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmBlueprint(id!),
    onSuccess: invalidate,
  })

  if (!id) {
    return (
      <PageShell title="故事蓝图" description="基于已确认简报，生成并确认故事蓝图组。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const run = blueprint?.latest_run ?? null
  const runBusy = isStageRunInProgress(run) || generateMutation.isPending
  const hasCandidate = Boolean(blueprint?.candidate)
  const hasCommitted = Boolean(blueprint?.committed)
  const nextCta = id ? resolveNextStageCta(id, 'blueprint') : null
  const generateLabel = hasCandidate || hasCommitted ? '重新生成' : '生成蓝图'
  const canGenerate = hasCommittedBrief && Boolean(blueprint) && !runBusy
  const canConfirm = hasCandidate && !runBusy
  const actionError =
    generateMutation.isError
      ? formatApiError(generateMutation.error)
      : confirmMutation.isError
        ? formatApiError(confirmMutation.error)
        : null

  const candidateArt = pickArtifact(blueprint?.candidate, activeTab)
  const committedArt = pickArtifact(blueprint?.committed, activeTab)
  const tabLabel =
    BLUEPRINT_TABS.find((tab) => tab.id === activeTab)?.label ?? activeTab

  const actions = (
    <>
      <Button
        type="button"
        variant="secondary"
        loading={generateMutation.isPending}
        disabled={!canGenerate}
        onClick={() => generateMutation.mutate()}
      >
        {generateLabel}
      </Button>
      {canConfirm ? (
        <Button
          type="button"
          loading={confirmMutation.isPending}
          disabled={confirmMutation.isPending || runBusy}
          onClick={() => confirmMutation.mutate()}
        >
          确认采用
        </Button>
      ) : null}
    </>
  )

  return (
    <PageShell title="故事蓝图" description="基于已确认简报，生成并确认故事蓝图组。" actions={actions}>
      {blueprintQuery.isLoading || topicQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载蓝图状态…</p>
      ) : null}

      {blueprintQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(blueprintQuery.error)}</p>
      ) : null}

      {topicQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(topicQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {blueprint && !topicQuery.isLoading && !topicQuery.isError ? (
        <div className="space-y-4">
          <StageStatusPanel
            run={run}
            idleHint={
              hasCommittedBrief ? '尚未生成蓝图，点击「生成蓝图」开始。' : undefined
            }
            generateSucceededHint={
              hasCandidate && !hasCommitted
                ? '生成已完成，可预览候选并确认采用。'
                : undefined
            }
            prerequisite={
              !hasCommittedBrief
                ? {
                    message: '请先在「选题定调」确认项目简报后，再生成故事蓝图。',
                    to: `/projects/${id}/topic`,
                    linkLabel: '去选题定调',
                  }
                : null
            }
            nextStep={
              hasCommitted && nextCta
                ? {
                    to: nextCta.to,
                    label: nextCta.label,
                    hint: '蓝图已确认，可进入下一阶段继续创作。',
                  }
                : null
            }
          />

          <Tabs
            items={BLUEPRINT_TABS.map((tab) => ({ id: tab.id, label: tab.label }))}
            value={activeTab}
            onChange={(next) => setActiveTab(next as BlueprintTabId)}
          />

          {committedArt ? (
            <ArtifactPanel artifact={committedArt} heading={`已确认 · ${tabLabel}`} />
          ) : null}

          {candidateArt ? (
            <ArtifactPanel artifact={candidateArt} heading={`候选 · ${tabLabel}`} />
          ) : null}

          {!committedArt && !candidateArt ? (
            <section className="sf-panel p-4">
              <p className="text-sm text-ink-muted">当前标签暂无内容。</p>
            </section>
          ) : null}
        </div>
      ) : null}
    </PageShell>
  )
}

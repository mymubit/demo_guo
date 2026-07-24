import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { ArtifactPreview } from '@/components/ArtifactPreview'
import { Button } from '@/components/ui/Button'
import {
  isStageRunInProgress,
  StageStatusPanel,
} from '@/components/workflow/StageStatusPanel'
import { formatApiError } from '@/services/errors'
import {
  confirmTopicBrief,
  generateTopicBrief,
  getTopicState,
  saveTopicDraft,
} from '@/services/v3/topic'
import type { ArtifactVersion, CommandRunSummary } from '@/types/v3/domain'
import { resolveNextStageCta } from './projectLabels'

function readStringField(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key]
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function BriefSummary({ artifact, heading }: { artifact: ArtifactVersion; heading: string }) {
  const payload = artifact.payload ?? {}
  const title = readStringField(payload, 'title')
  const selling =
    readStringField(payload, 'core_idea') ??
    readStringField(payload, 'hook_concept') ??
    readStringField(payload, 'selling_point')
  const audience = readStringField(payload, 'target_audience')
  const hasSummary = Boolean(title || selling || audience)

  return (
    <section className="sf-panel space-y-3 p-4">
      <h2 className="text-sm font-semibold text-ink">{heading}</h2>
      {hasSummary ? (
        <dl className="grid gap-3 sm:grid-cols-2">
          {title ? (
            <div>
              <dt className="text-xs text-ink-faint">标题</dt>
              <dd className="mt-1 text-sm text-ink">{title}</dd>
            </div>
          ) : null}
          {selling ? (
            <div className="sm:col-span-2">
              <dt className="text-xs text-ink-faint">卖点</dt>
              <dd className="mt-1 text-sm text-ink">{selling}</dd>
            </div>
          ) : null}
          {audience ? (
            <div>
              <dt className="text-xs text-ink-faint">目标受众</dt>
              <dd className="mt-1 text-sm text-ink">{audience}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
      <ArtifactPreview payload={payload} />
    </section>
  )
}

function formatPayloadText(payload: Record<string, unknown> | null | undefined): string {
  if (!payload) return '{\n\n}'
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return '{\n\n}'
  }
}

export function TopicPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [draftText, setDraftText] = useState('')
  const [draftParseError, setDraftParseError] = useState<string | null>(null)
  const [useDraftOnConfirm, setUseDraftOnConfirm] = useState(false)

  const topicQuery = useQuery({
    queryKey: ['v3', 'topic', id],
    queryFn: () => getTopicState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const topic = topicQuery.data

  useEffect(() => {
    if (!topic) return
    const source = topic.draft?.payload ?? topic.candidate?.payload ?? topic.committed?.payload
    setDraftText(formatPayloadText(source))
    setDraftParseError(null)
  }, [topic?.draft?.id, topic?.candidate?.id, topic?.committed?.id, topic?.draft?.created_at])

  const invalidateTopic = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'topic', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const generateMutation = useMutation({
    mutationFn: () => generateTopicBrief(id!),
    onSuccess: invalidateTopic,
  })

  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmTopicBrief(id!, useDraftOnConfirm ? { use_draft: true } : undefined),
    onSuccess: invalidateTopic,
  })

  const draftMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => saveTopicDraft(id!, payload),
    onSuccess: invalidateTopic,
  })

  const handleSaveDraft = () => {
    setDraftParseError(null)
    try {
      const parsed = JSON.parse(draftText) as unknown
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        setDraftParseError('草稿须为 JSON 对象')
        return
      }
      draftMutation.mutate(parsed as Record<string, unknown>)
    } catch {
      setDraftParseError('草稿 JSON 无法解析，请检查格式')
    }
  }

  if (!id) {
    return (
      <PageShell title="选题定调" description="确定题材方向与创作基调。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const run = topic?.latest_run ?? null
  const runBusy = isStageRunInProgress(run) || generateMutation.isPending
  const hasBrief = Boolean(topic?.candidate || topic?.committed)
  const generateLabel = hasBrief ? '重新生成' : '生成简报'
  const canConfirm = Boolean(topic?.candidate) || (useDraftOnConfirm && Boolean(topic?.draft))
  const nextCta = id ? resolveNextStageCta(id, 'topic') : null
  const actionError =
    generateMutation.isError
      ? formatApiError(generateMutation.error)
      : confirmMutation.isError
        ? formatApiError(confirmMutation.error)
        : draftMutation.isError
          ? formatApiError(draftMutation.error)
          : null

  const actions = (
    <>
      <Button
        type="button"
        variant="secondary"
        loading={generateMutation.isPending}
        disabled={runBusy || !topic}
        onClick={() => generateMutation.mutate()}
      >
        {generateLabel}
      </Button>
      {canConfirm ? (
        <Button
          type="button"
          loading={confirmMutation.isPending}
          disabled={runBusy || confirmMutation.isPending}
          onClick={() => confirmMutation.mutate()}
        >
          确认采用
        </Button>
      ) : null}
    </>
  )

  return (
    <PageShell title="选题定调" description="确定题材方向与创作基调。" actions={actions}>
      {topicQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载选题状态…</p> : null}

      {topicQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(topicQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {topic ? (
        <div className="space-y-4">
          <StageStatusPanel
            run={run}
            idleHint="新建项目后会自动开始生成选题简报；若未开始，可点击「生成简报」。"
            generateSucceededHint={
              topic.candidate && !topic.committed
                ? '生成已完成，可预览候选并确认采用。'
                : undefined
            }
            nextStep={
              topic.committed && nextCta
                ? {
                    to: nextCta.to,
                    label: nextCta.label,
                    hint: '选题已确认，可进入下一阶段继续创作。',
                  }
                : null
            }
          />

          {topic.committed ? (
            <BriefSummary artifact={topic.committed} heading="已确认简报" />
          ) : null}

          {topic.candidate ? (
            <BriefSummary artifact={topic.candidate} heading="候选简报" />
          ) : null}

          <section className="sf-panel space-y-3 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-ink">编辑草稿</h2>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                loading={draftMutation.isPending}
                disabled={draftMutation.isPending}
                onClick={handleSaveDraft}
              >
                保存草稿
              </Button>
            </div>
            <p className="text-xs text-ink-faint">以 JSON 编辑项目简报内容；保存后可在确认时选择使用草稿。</p>
            <textarea
              aria-label="选题草稿"
              className="min-h-48 w-full rounded-md border border-border bg-surface px-3 py-2 font-mono text-xs text-ink"
              value={draftText}
              onChange={(event) => {
                setDraftText(event.target.value)
                setDraftParseError(null)
              }}
            />
            {draftParseError ? <p className="text-sm text-danger">{draftParseError}</p> : null}
            {topic.draft ? (
              <label className="inline-flex items-center gap-2 text-sm text-ink-muted">
                <input
                  type="checkbox"
                  checked={useDraftOnConfirm}
                  onChange={(event) => setUseDraftOnConfirm(event.target.checked)}
                  className="h-4 w-4 rounded border-border"
                />
                确认时使用草稿
              </label>
            ) : null}
          </section>
        </div>
      ) : null}
    </PageShell>
  )
}

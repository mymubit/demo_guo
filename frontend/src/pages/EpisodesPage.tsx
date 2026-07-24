import { useMemo, useState } from 'react'
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
import { getBlueprintState } from '@/services/v3/blueprint'
import {
  confirmEpisodePlan,
  generateEpisodePlan,
  getEpisodesState,
  reviseEpisodePlan,
} from '@/services/v3/episodes'
import { resolveNextStageCta, STAGE_LABEL } from './projectLabels'

type EpisodeCardData = {
  episode: number
  title: string | null
  hook: string | null
  emotion: string | null
  raw: Record<string, unknown>
}

function readStringField(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key]
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function readEmotionSummary(payload: Record<string, unknown>): string | null {
  const nodes = payload.emotion_nodes
  if (!nodes || typeof nodes !== 'object' || Array.isArray(nodes)) return null
  const emotions: string[] = []
  for (const node of Object.values(nodes as Record<string, unknown>)) {
    if (!node || typeof node !== 'object' || Array.isArray(node)) continue
    const emotion = readStringField(node as Record<string, unknown>, 'emotion')
    if (emotion) emotions.push(emotion)
  }
  return emotions.length > 0 ? emotions.join(' · ') : null
}

function extractEpisodes(payload: Record<string, unknown> | null | undefined): EpisodeCardData[] {
  if (!payload) return []
  const list = payload.episodes
  if (!Array.isArray(list)) return []
  return list
    .map((item): EpisodeCardData | null => {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return null
      const row = item as Record<string, unknown>
      const episodeRaw = row.episode ?? row.episode_number
      const episode = typeof episodeRaw === 'number' ? episodeRaw : Number(episodeRaw)
      if (!Number.isFinite(episode) || episode < 1) return null
      return {
        episode,
        title: readStringField(row, 'title'),
        hook:
          readStringField(row, 'opening_hook') ??
          readStringField(row, 'ending_hook') ??
          readStringField(row, 'hook'),
        emotion: readEmotionSummary(row),
        raw: row,
      }
    })
    .filter((item): item is EpisodeCardData => item !== null)
    .sort((a, b) => a.episode - b.episode)
}

function EpisodeCard({
  item,
  selectable,
  selected,
  onToggle,
}: {
  item: EpisodeCardData
  selectable: boolean
  selected: boolean
  onToggle: () => void
}) {
  const hasSummary = Boolean(item.title || item.hook || item.emotion)

  return (
    <article className="sf-panel space-y-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {selectable ? (
            <label className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
              <input
                type="checkbox"
                checked={selected}
                onChange={onToggle}
                aria-label={`第 ${item.episode} 集`}
                className="h-4 w-4 rounded border-border"
              />
              第 {item.episode} 集
            </label>
          ) : (
            <h3 className="text-sm font-semibold text-ink">第 {item.episode} 集</h3>
          )}
          {item.title ? <p className="mt-1 text-sm text-ink">{item.title}</p> : null}
        </div>
      </div>

      {hasSummary ? (
        <dl className="grid gap-2">
          {item.hook ? (
            <div>
              <dt className="text-xs text-ink-faint">钩子</dt>
              <dd className="mt-1 text-sm text-ink">{item.hook}</dd>
            </div>
          ) : null}
          {item.emotion ? (
            <div>
              <dt className="text-xs text-ink-faint">情绪</dt>
              <dd className="mt-1 text-sm text-ink">{item.emotion}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}

      <ArtifactPreview payload={item.raw} />
    </article>
  )
}

export function EpisodesPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [selectedEpisodes, setSelectedEpisodes] = useState<number[]>([])

  const episodesQuery = useQuery({
    queryKey: ['v3', 'episodes', id],
    queryFn: () => getEpisodesState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const blueprintQuery = useQuery({
    queryKey: ['v3', 'blueprint', id],
    queryFn: () => getBlueprintState(id!),
    enabled: Boolean(id),
  })

  const episodes = episodesQuery.data
  const hasCommittedBlueprint = Boolean(blueprintQuery.data?.committed)

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'episodes', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const generateMutation = useMutation({
    mutationFn: () => generateEpisodePlan(id!),
    onSuccess: invalidate,
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmEpisodePlan(id!),
    onSuccess: invalidate,
  })

  const reviseMutation = useMutation({
    mutationFn: (episodeNumbers: number[]) =>
      reviseEpisodePlan(id!, { episode_numbers: episodeNumbers }),
    onSuccess: () => {
      setSelectedEpisodes([])
      invalidate()
    },
  })

  const candidateEpisodes = useMemo(
    () => extractEpisodes(episodes?.candidate?.payload),
    [episodes?.candidate?.payload],
  )
  const committedEpisodes = useMemo(
    () => extractEpisodes(episodes?.committed?.payload),
    [episodes?.committed?.payload],
  )

  if (!id) {
    return (
      <PageShell title="分集规划" description="基于已确认蓝图，生成并确认全剧分集规划。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const run = episodes?.latest_run ?? null
  const runBusy =
    isStageRunInProgress(run) ||
    generateMutation.isPending ||
    reviseMutation.isPending
  const hasCandidate = Boolean(episodes?.candidate)
  const hasCommitted = Boolean(episodes?.committed)
  const nextCta = id ? resolveNextStageCta(id, 'episodes') : null
  const canGenerate = hasCommittedBlueprint && Boolean(episodes) && !runBusy
  const canConfirm = hasCandidate && !runBusy
  const canRevise = hasCommitted && selectedEpisodes.length > 0 && !runBusy
  const actionError =
    generateMutation.isError
      ? formatApiError(generateMutation.error)
      : confirmMutation.isError
        ? formatApiError(confirmMutation.error)
        : reviseMutation.isError
          ? formatApiError(reviseMutation.error)
          : null

  const toggleEpisode = (episode: number) => {
    setSelectedEpisodes((prev) =>
      prev.includes(episode) ? prev.filter((n) => n !== episode) : [...prev, episode].sort((a, b) => a - b),
    )
  }

  const actions = (
    <>
      <Button
        type="button"
        variant="secondary"
        loading={generateMutation.isPending}
        disabled={!canGenerate}
        onClick={() => generateMutation.mutate()}
      >
        生成全剧规划
      </Button>
      <Button
        type="button"
        variant="secondary"
        loading={reviseMutation.isPending}
        disabled={!canRevise}
        onClick={() => reviseMutation.mutate(selectedEpisodes)}
      >
        局部修订
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
    <PageShell title="分集规划" description="基于已确认蓝图，生成并确认全剧分集规划。" actions={actions}>
      {episodesQuery.isLoading || blueprintQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载分集状态…</p>
      ) : null}

      {episodesQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(episodesQuery.error)}</p>
      ) : null}

      {blueprintQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(blueprintQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {episodes && !blueprintQuery.isLoading && !blueprintQuery.isError ? (
        <div className="space-y-4">
          <StageStatusPanel
            run={run}
            idleHint={
              hasCommittedBlueprint ? '尚未生成分集规划，点击「生成全剧规划」开始。' : undefined
            }
            generateSucceededHint={
              hasCandidate && !hasCommitted
                ? '生成已完成，可预览候选并确认采用。'
                : undefined
            }
            prerequisite={
              !hasCommittedBlueprint
                ? {
                    message: '请先确认故事蓝图后，再生成分集规划。',
                    to: `/projects/${id}/blueprint`,
                    linkLabel: '去故事蓝图',
                  }
                : null
            }
            nextStep={
              hasCommitted && nextCta
                ? {
                    to: nextCta.to,
                    label: nextCta.label,
                    hint: '分集规划已确认，可进入下一阶段继续创作。',
                  }
                : null
            }
          >
            <p className="text-sm text-ink">
              当前阶段：{STAGE_LABEL[episodes.stage] ?? episodes.stage}
            </p>
            {hasCommitted ? (
              <p className="text-xs text-ink-faint">勾选已确认分集后，可对局部集数发起修订。</p>
            ) : null}
          </StageStatusPanel>

          {candidateEpisodes.length > 0 ? (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-ink">候选规划</h2>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {candidateEpisodes.map((item) => (
                  <EpisodeCard
                    key={`candidate-${item.episode}`}
                    item={item}
                    selectable={false}
                    selected={false}
                    onToggle={() => undefined}
                  />
                ))}
              </div>
            </section>
          ) : null}

          {committedEpisodes.length > 0 ? (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-ink">已确认规划</h2>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {committedEpisodes.map((item) => (
                  <EpisodeCard
                    key={`committed-${item.episode}`}
                    item={item}
                    selectable
                    selected={selectedEpisodes.includes(item.episode)}
                    onToggle={() => toggleEpisode(item.episode)}
                  />
                ))}
              </div>
            </section>
          ) : null}

          {!candidateEpisodes.length && !committedEpisodes.length && hasCommittedBlueprint ? (
            <section className="sf-panel p-4">
              <p className="text-sm text-ink-muted">暂无分集卡片可展示。</p>
            </section>
          ) : null}
        </div>
      ) : null}
    </PageShell>
  )
}

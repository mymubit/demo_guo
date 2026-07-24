import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { SceneListEditor } from '@/components/script/SceneListEditor'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import {
  isStageRunInProgress,
  StageStatusPanel,
} from '@/components/workflow/StageStatusPanel'
import { formatApiError } from '@/services/errors'
import { getEpisodesState } from '@/services/v3/episodes'
import {
  confirmScriptCandidate,
  generateScriptBatch,
  getScriptEpisode,
  getScriptsState,
  putScriptDraft,
} from '@/services/v3/scripts'
import type { ScriptDraftPayload, ScriptScene } from '@/types/v3/domain'
import { parseEpisodeNumber } from '@/utils/parseEpisodeHint'
import { resolveNextStageCta } from './projectLabels'

const AUTOSAVE_DEBOUNCE_MS = 1000
const DEFAULT_BATCH_END = 2
const SAVE_ERROR_FALLBACK = '草稿保存失败，请稍后重试'

function emptyScenes(): ScriptScene[] {
  return [{ id: 's1', heading: '', beats: [{ type: 'action', text: '' }] }]
}

function asScenes(payload: Record<string, unknown> | ScriptDraftPayload | null | undefined): ScriptScene[] | null {
  if (!payload || typeof payload !== 'object') return null
  const scenes = (payload as ScriptDraftPayload).scenes
  if (!Array.isArray(scenes)) return null
  return scenes.map((scene, index) => ({
    id: typeof scene.id === 'string' && scene.id ? scene.id : `s${index + 1}`,
    heading: typeof scene.heading === 'string' ? scene.heading : '',
    beats: Array.isArray(scene.beats)
      ? scene.beats.map((beat) => ({
          type: typeof beat.type === 'string' ? beat.type : 'action',
          text: typeof beat.text === 'string' ? beat.text : '',
          ...(typeof beat.character === 'string' ? { character: beat.character } : {}),
        }))
      : [],
  }))
}

function episodeSliceToScenes(slice: Record<string, unknown> | null | undefined): ScriptScene[] {
  const structured = asScenes(slice ?? null)
  if (structured && structured.length > 0) return structured
  if (!slice) return emptyScenes()
  const script = typeof slice.script === 'string' ? slice.script : ''
  const title = typeof slice.title === 'string' ? slice.title : ''
  if (!script) return emptyScenes()
  return [
    {
      id: 'imported',
      heading: title || '正文',
      beats: [{ type: 'action', text: script }],
    },
  ]
}

function extractEpisodeNumbers(payload: Record<string, unknown> | null | undefined): number[] {
  if (!payload) return []
  const list = payload.episodes
  if (!Array.isArray(list)) return []
  return list
    .map((item) => {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return null
      const row = item as Record<string, unknown>
      const raw = row.episode ?? row.episode_number
      const num = typeof raw === 'number' ? raw : Number(raw)
      return Number.isFinite(num) && num >= 1 ? num : null
    })
    .filter((n): n is number => n !== null)
    .sort((a, b) => a - b)
}

function countScriptChars(payload: Record<string, unknown> | null | undefined): number {
  if (!payload) return 0
  const list = payload.episodes
  if (!Array.isArray(list)) return 0
  let total = 0
  for (const item of list) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) continue
    const row = item as Record<string, unknown>
    if (typeof row.script === 'string') {
      total += row.script.length
      continue
    }
    const scenes = asScenes(row)
    if (!scenes) continue
    for (const scene of scenes) {
      total += scene.heading.length
      for (const beat of scene.beats) {
        total += beat.text.length
        if (beat.character) total += beat.character.length
      }
    }
  }
  return total
}

function scenesEqual(a: ScriptScene[], b: ScriptScene[]): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function episodeFromSearchParams(searchParams: URLSearchParams): number | null {
  const raw = searchParams.get('episode') ?? searchParams.get('ep')
  if (!raw) return null
  return parseEpisodeNumber(raw)
}

export function ScriptEditorPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()

  const episodeFromQuery = episodeFromSearchParams(searchParams)
  const selectedEpisode = episodeFromQuery ?? 1
  const findingKey = searchParams.get('finding')
  const showJumpHint = Boolean(findingKey?.trim()) && episodeFromQuery === null

  const [scenes, setScenes] = useState<ScriptScene[]>(emptyScenes())
  const [dirty, setDirty] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const skipNextAutosave = useRef(true)
  const hydratedEpisode = useRef<number | null>(null)
  const debounceTimerRef = useRef<number | null>(null)
  const inFlightRef = useRef<Promise<boolean> | null>(null)
  const retryTimerRef = useRef<number | null>(null)

  const scenesRef = useRef(scenes)
  const selectedEpisodeRef = useRef(selectedEpisode)
  const dirtyRef = useRef(dirty)

  useEffect(() => {
    scenesRef.current = scenes
  }, [scenes])

  useEffect(() => {
    selectedEpisodeRef.current = selectedEpisode
  }, [selectedEpisode])

  useEffect(() => {
    dirtyRef.current = dirty
  }, [dirty])

  const episodesQuery = useQuery({
    queryKey: ['v3', 'episodes', id],
    queryFn: () => getEpisodesState(id!),
    enabled: Boolean(id),
  })

  const scriptsQuery = useQuery({
    queryKey: ['v3', 'scripts', id],
    queryFn: () => getScriptsState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const episodeQuery = useQuery({
    queryKey: ['v3', 'scripts', id, 'episode', selectedEpisode],
    queryFn: () => getScriptEpisode(id!, selectedEpisode),
    enabled: Boolean(id),
  })

  const scripts = scriptsQuery.data
  const hasCommittedPlan = Boolean(episodesQuery.data?.committed)

  const episodeNumbers = useMemo(() => {
    const fromPlan = extractEpisodeNumbers(episodesQuery.data?.committed?.payload)
    if (fromPlan.length > 0) return fromPlan
    const fromScripts = new Set<number>()
    for (const n of extractEpisodeNumbers(scripts?.committed?.payload)) fromScripts.add(n)
    for (const n of extractEpisodeNumbers(scripts?.candidate?.payload)) fromScripts.add(n)
    for (const d of scripts?.drafts ?? []) fromScripts.add(d.episode_number)
    fromScripts.add(selectedEpisode)
    return Array.from(fromScripts).sort((a, b) => a - b)
  }, [
    episodesQuery.data?.committed?.payload,
    scripts?.committed?.payload,
    scripts?.candidate?.payload,
    scripts?.drafts,
    selectedEpisode,
  ])

  const draftEpisodes = useMemo(
    () => new Set((scripts?.drafts ?? []).map((d) => d.episode_number)),
    [scripts?.drafts],
  )
  const committedEpisodes = useMemo(
    () => new Set(extractEpisodeNumbers(scripts?.committed?.payload)),
    [scripts?.committed?.payload],
  )

  const flushAutosave = (): Promise<boolean> => {
    if (inFlightRef.current) return inFlightRef.current
    if (!id || !dirtyRef.current) return Promise.resolve(true)

    const episode = selectedEpisodeRef.current
    const payload = { scenes: scenesRef.current }
    setSaveError(null)

    const promise = putScriptDraft(id, episode, payload)
      .then(() => {
        void queryClient.invalidateQueries({ queryKey: ['v3', 'scripts', id] })
        void queryClient.invalidateQueries({
          queryKey: ['v3', 'scripts', id, 'episode', episode],
        })
        if (selectedEpisodeRef.current === episode) {
          dirtyRef.current = false
          setDirty(false)
          setSaveError(null)
        }
        return true
      })
      .catch((error: unknown) => {
        const message = formatApiError(error) || SAVE_ERROR_FALLBACK
        setSaveError(message)
        dirtyRef.current = true
        setDirty(true)
        if (retryTimerRef.current !== null) {
          window.clearTimeout(retryTimerRef.current)
        }
        retryTimerRef.current = window.setTimeout(() => {
          retryTimerRef.current = null
          if (
            dirtyRef.current &&
            selectedEpisodeRef.current === episode &&
            !inFlightRef.current
          ) {
            void flushAutosave()
          }
        }, AUTOSAVE_DEBOUNCE_MS)
        return false
      })
      .finally(() => {
        inFlightRef.current = null
      })

    inFlightRef.current = promise
    return promise
  }

  useEffect(() => {
    if (!episodeQuery.data) return
    if (episodeQuery.data.episode_number !== selectedEpisode) return
    if (hydratedEpisode.current === selectedEpisode && dirty) return

    const fromDraft = asScenes(episodeQuery.data.draft?.payload ?? null)
    const next =
      fromDraft && fromDraft.length > 0
        ? fromDraft
        : episodeSliceToScenes(episodeQuery.data.committed ?? episodeQuery.data.candidate)
    skipNextAutosave.current = true
    hydratedEpisode.current = selectedEpisode
    setScenes(next)
    setDirty(false)
    setSaveError(null)
  }, [episodeQuery.data, selectedEpisode, dirty])

  useEffect(() => {
    if (!id || !dirty) return
    if (skipNextAutosave.current) {
      skipNextAutosave.current = false
      return
    }

    debounceTimerRef.current = window.setTimeout(() => {
      debounceTimerRef.current = null
      void flushAutosave()
    }, AUTOSAVE_DEBOUNCE_MS)

    return () => {
      if (debounceTimerRef.current !== null) {
        window.clearTimeout(debounceTimerRef.current)
        debounceTimerRef.current = null
      }
    }
    // flushAutosave 通过 refs 读取最新值，避免切集时闭包过期
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 刻意依赖 dirty/scenes/episode
  }, [id, selectedEpisode, scenes, dirty, queryClient])

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'scripts', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const generateMutation = useMutation({
    mutationFn: () =>
      generateScriptBatch(id!, {
        start: 1,
        end: Math.min(DEFAULT_BATCH_END, episodeNumbers[episodeNumbers.length - 1] ?? DEFAULT_BATCH_END),
      }),
    onSuccess: invalidate,
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmScriptCandidate(id!, { use_drafts: false }),
    onSuccess: invalidate,
  })

  if (!id) {
    return (
      <PageShell title="正文编辑" description="按集编辑结构化场景，并确认 AI 正文候选。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const run = scripts?.latest_run ?? null
  const runBusy =
    isStageRunInProgress(run) || generateMutation.isPending || confirmMutation.isPending
  const hasCandidate = Boolean(scripts?.candidate)
  const hasCommittedScripts = Boolean(scripts?.committed)
  const nextCta = id ? resolveNextStageCta(id, 'writing') : null
  const canGenerate = hasCommittedPlan && Boolean(scripts) && !runBusy
  const canConfirm = hasCandidate && !runBusy

  const candidateEpisodes = extractEpisodeNumbers(scripts?.candidate?.payload)
  const candidateChars = countScriptChars(scripts?.candidate?.payload)
  const committedChars = countScriptChars(scripts?.committed?.payload)

  const actionError =
    generateMutation.isError
      ? formatApiError(generateMutation.error)
      : confirmMutation.isError
        ? formatApiError(confirmMutation.error)
        : null

  const selectEpisode = async (episode: number) => {
    if (episode === selectedEpisodeRef.current) return

    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }
    if (retryTimerRef.current !== null) {
      window.clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }

    if (dirtyRef.current || inFlightRef.current) {
      const ok = await flushAutosave()
      if (!ok || dirtyRef.current) return
    }

    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('episode', String(episode))
      next.delete('ep')
      return next
    })
    dirtyRef.current = false
    setDirty(false)
    setSaveError(null)
    hydratedEpisode.current = null
  }

  const handleScenesChange = (next: ScriptScene[]) => {
    if (scenesEqual(next, scenes)) return
    skipNextAutosave.current = false
    setScenes(next)
    setDirty(true)
  }

  const batchEnd = Math.min(
    DEFAULT_BATCH_END,
    episodeNumbers[episodeNumbers.length - 1] ?? DEFAULT_BATCH_END,
  )

  const actions = (
    <>
      <Link
        to={`/projects/${id}/episodes`}
        className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-surface px-4 text-sm font-medium text-ink hover:bg-canvas-muted"
      >
        分集规划
      </Link>
    </>
  )

  return (
    <PageShell title="正文编辑" description="按集编辑结构化场景，并确认 AI 正文候选。" actions={actions}>
      {episodesQuery.isLoading || scriptsQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载正文状态…</p>
      ) : null}

      {episodesQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(episodesQuery.error)}</p>
      ) : null}
      {scriptsQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(scriptsQuery.error)}</p>
      ) : null}
      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}
      {showJumpHint ? (
        <p className="mb-3 text-sm text-ink-muted" data-testid="editor-jump-hint">
          未定位到场次，已打开编辑器
        </p>
      ) : null}

      {scripts && !episodesQuery.isLoading ? (
        <div className="grid gap-4 lg:grid-cols-[14rem_minmax(0,1fr)_16rem]">
          <aside className="sf-panel space-y-2 p-3">
            <h2 className="text-sm font-semibold text-ink">集数</h2>
            <ul className="space-y-1">
              {episodeNumbers.map((episode) => {
                const isActive = episode === selectedEpisode
                const hasDraft = draftEpisodes.has(episode)
                const hasCommitted = committedEpisodes.has(episode)
                return (
                  <li key={episode}>
                    <button
                      type="button"
                      onClick={() => {
                        void selectEpisode(episode)
                      }}
                      className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm ${
                        isActive ? 'bg-action/10 text-ink font-semibold' : 'text-ink-muted hover:bg-canvas-muted'
                      }`}
                    >
                      <span>第 {episode} 集</span>
                      <span className="text-xs text-ink-faint">
                        {hasDraft ? '有草稿' : hasCommitted ? '已确认' : '未写'}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </aside>

          <section className="min-w-0 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-ink">第 {selectedEpisode} 集场景</h2>
              {saveError ? (
                <p className="text-xs text-danger">{saveError}</p>
              ) : (
                <p className="text-xs text-ink-faint">{dirty ? '正在保存…' : '草稿自动保存'}</p>
              )}
            </div>
            {episodeQuery.isLoading ? (
              <p className="text-sm text-ink-muted">正在加载本集…</p>
            ) : (
              <SceneListEditor scenes={scenes} onChange={handleScenesChange} />
            )}
          </section>

          <aside className="space-y-3">
            <StageStatusPanel
              run={run}
              idleHint={
                hasCommittedPlan
                  ? `可生成本批正文（默认第 1–${batchEnd} 集）。`
                  : undefined
              }
              generateSucceededHint={
                hasCandidate ? '生成已完成，可预览候选并确认采用。' : undefined
              }
              prerequisite={
                !hasCommittedPlan
                  ? {
                      message: '请先确认分集规划后，再生成正文。',
                      to: `/projects/${id}/episodes`,
                      linkLabel: '去分集规划',
                    }
                  : null
              }
              nextStep={
                hasCommittedScripts && nextCta
                  ? {
                      to: nextCta.to,
                      label: nextCta.label,
                      hint: '正文已确认，可进入下一阶段继续创作。',
                    }
                  : null
              }
            />

            <section className="sf-panel space-y-3 p-4">
              <h2 className="text-sm font-semibold text-ink">AI 正文</h2>

              {hasCandidate ? (
                <div className="space-y-1 rounded-md border border-border bg-canvas-muted/40 px-3 py-2 text-sm text-ink">
                  <p>候选集：{candidateEpisodes.join('、') || '—'}</p>
                  <p>候选约 {candidateChars} 字</p>
                  <p className="text-ink-muted">已确认约 {committedChars} 字</p>
                </div>
              ) : null}

              <div className="flex flex-col gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  loading={generateMutation.isPending}
                  disabled={!canGenerate}
                  onClick={() => generateMutation.mutate()}
                >
                  生成本批（1–{batchEnd}）
                </Button>
                <Button
                  type="button"
                  loading={confirmMutation.isPending}
                  disabled={!canConfirm}
                  onClick={() => confirmMutation.mutate()}
                >
                  确认采用
                </Button>
              </div>
            </section>
          </aside>
        </div>
      ) : null}
    </PageShell>
  )
}

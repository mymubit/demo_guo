import { useMemo, useState, useEffect } from 'react'
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Circle,
  Filter,
  Layers,
  Sparkles,
} from 'lucide-react'
import { formatPayloadText } from '../shared/PayloadInspector'
import {
  STAGE_LABELS,
  STAGE_ORDER,
  extractStageSummary,
  normalizeSixStage,
} from '../../utils/outlineStructure'

function parseEpisodeNum(item) {
  if (!item || typeof item !== 'object') return 0
  const raw = item.episode_num ?? item.episodeNumber ?? item.episode_no ?? item.episode ?? item.episode_id
  if (typeof raw === 'number') return raw
  const text = String(raw || '').trim()
  const match = text.match(/(\d+)/)
  return match ? Number(match[1]) : 0
}

function episodeHasContent(item) {
  if (!item) return false
  if (item.missing) return false
  if (String(item.goal_conflict || item.core_event || item.summary || item.oneLineSummary || '').trim()) return true
  if (item.ending_hook || item.end_hook || item.subtitle || item.title) return true
  if (item.four_segment_structure || item.ev_et_tp || item.emotion_markers || item.emotion_nodes) return true
  if ((item.structure || item.sections || []).length) return true
  return false
}

function normalizeCardEpisode(card) {
  if (!card) return null
  const num = card.episode_no || parseEpisodeNum(card)
  if (!num) return null
  return { ...card, episode_no: num }
}

function buildEpisodeMap(rawArtifact, viewBlock, outlineProgress) {
  const byNum = new Map()

  const rawList = rawArtifact?.episode_outlines || rawArtifact?.episodes || []
  if (Array.isArray(rawList)) {
    rawList.forEach((item) => {
      const num = parseEpisodeNum(item)
      if (num) byNum.set(num, { ...item, episode_no: num })
    })
  }

  const cardList = viewBlock?.episodes || []
  if (Array.isArray(cardList)) {
    cardList.forEach((card) => {
      const normalized = normalizeCardEpisode(card)
      if (normalized?.episode_no && !normalized.missing) {
        byNum.set(normalized.episode_no, normalized)
      }
    })
  }

  const batches = viewBlock?.episode_batches || []
  batches.forEach((batch) => {
    (batch.episodes || []).forEach((ep) => {
      const normalized = normalizeCardEpisode(ep)
      if (normalized?.episode_no && !normalized.missing && episodeHasContent(normalized)) {
        byNum.set(normalized.episode_no, normalized)
      }
    })
  })

  const generatedFromProgress = new Set(outlineProgress?.generated_episodes || [])
  generatedFromProgress.forEach((num) => {
    if (!byNum.has(num)) {
      byNum.set(num, { episode_no: num, _progressOnly: true })
    }
  })

  return byNum
}

function EmotionTags({ item }) {
  const emotions = item.emotions?.length
    ? item.emotions
    : (item.sections || []).filter((s) => /EV|ET|TP|情绪/.test(String(s.label)))
  if (!emotions.length) return null
  return (
    <div className="flex flex-wrap gap-2">
      {emotions.map((e, i) => (
        <span
          key={`emo-${i}`}
          className="rounded-lg bg-cyan-500/10 border border-cyan-500/20 px-2.5 py-1 text-xs text-cyan-200"
        >
          <span className="font-semibold text-cyan-400">{e.label}</span>
          {e.text ? `: ${e.text}` : ''}
        </span>
      ))}
    </div>
  )
}

function EpisodeDetail({ episode, totalEpisodes, onRequestGenerate }) {
  if (!episode) {
    return (
      <div className="flex h-full min-h-[280px] items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-8 text-center">
        <p className="text-sm text-slate-500">点击左侧集号查看分集大纲详情</p>
      </div>
    )
  }

  if (!episode.generated) {
    return (
      <div className="flex h-full min-h-[280px] flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-8 text-center">
        <Circle className="h-10 w-10 text-slate-600" strokeWidth={1.5} />
        <div>
          <p className="text-lg font-semibold text-slate-300">第 {episode.num} 集 · 尚未生成</p>
          <p className="text-sm text-slate-500 mt-1">共 {totalEpisodes} 集，可在上方配置批次后执行生成</p>
        </div>
        {onRequestGenerate ? (
          <button
            type="button"
            onClick={() => onRequestGenerate(episode.num)}
            className="text-xs font-medium text-gold-400 hover:text-gold-300 border border-gold-500/30 rounded-lg px-3 py-1.5"
          >
            设为下一批生成范围
          </button>
        ) : null}
      </div>
    )
  }

  const data = episode.data || {}
  const structure = data.structure?.length
    ? data.structure
    : (data.sections || []).filter((s) => !/EV|ET|TP|情绪/.test(String(s.label)))
  const hook = data.subtitle || data.ending_hook || data.end_hook || ''

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] overflow-hidden">
      <div className="flex items-center gap-3 border-b border-white/10 bg-gradient-to-r from-gold-500/10 to-transparent px-5 py-4">
        <div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-gold-500 to-gold-600 text-white shadow-lg shadow-gold-500/20">
          <span className="text-[9px] font-medium uppercase opacity-80">EP</span>
          <span className="text-base font-bold tabular-nums">{episode.num}</span>
        </div>
        <div className="min-w-0">
          <h4 className="text-base font-bold text-white">{data.title || `第 ${episode.num} 集`}</h4>
          {(data.tags || []).length ? (
            <div className="flex flex-wrap gap-1 mt-1">
              {data.tags.map((tag, i) => (
                <span key={`tag-${i}`} className="text-[10px] text-gold-300/90 bg-gold-500/10 px-1.5 py-0.5 rounded">
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>
      <div className="p-5 space-y-4 max-h-[min(52vh,520px)] overflow-y-auto scrollbar-thin">
        {hook ? (
          <div className="rounded-xl border-l-[3px] border-amber-500/60 bg-amber-500/8 px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-300/90 mb-1">集末钩子</p>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{hook}</p>
          </div>
        ) : null}
        <EmotionTags item={data} />
        {structure.length ? (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">本集结构</p>
            {structure.map((seg, i) => (
              <div key={`seg-${i}`} className="rounded-lg bg-white/[0.03] border border-white/5 px-3 py-2.5">
                <p className="text-xs font-medium text-gold-300/90">{seg.label}</p>
                <p className="text-sm text-slate-300 mt-1 leading-relaxed whitespace-pre-wrap">{seg.text}</p>
              </div>
            ))}
          </div>
        ) : data.goal_conflict ? (
          <div className="rounded-lg bg-white/[0.03] border border-white/5 px-3 py-2.5">
            <p className="text-xs font-medium text-gold-300/90">目标与冲突</p>
            <p className="text-sm text-slate-300 mt-1 leading-relaxed">{data.goal_conflict}</p>
          </div>
        ) : data._progressOnly ? (
          <p className="text-sm text-slate-500">该集已标记为已生成，刷新页面后可加载完整内容。</p>
        ) : null}
      </div>
    </article>
  )
}

function rangeForEpisode(num, batchSize, total) {
  const size = batchSize || 10
  const start = Math.floor((num - 1) / size) * size + 1
  const end = Math.min(start + size - 1, total)
  return `${start}-${end}`
}

export default function PlotArchitectOutput({
  rawArtifact,
  outputView,
  outlineProgress,
  totalEpisodes = 60,
  batchSize = 10,
  onSelectRange,
  onGenerateStructure,
  structureLoading = false,
}) {
  const viewBlock = useMemo(() => {
    const blocks = outputView?.blocks || []
    return blocks.find((b) => b.type === 'series_outline') || null
  }, [outputView])

  const episodeMap = useMemo(
    () => buildEpisodeMap(rawArtifact, viewBlock, outlineProgress),
    [rawArtifact, viewBlock, outlineProgress],
  )

  const planned = totalEpisodes || viewBlock?.total_episodes || outlineProgress?.expected || 60
  const generatedNums = useMemo(() => {
    const nums = []
    for (let n = 1; n <= planned; n += 1) {
      const data = episodeMap.get(n)
      const fromProgress = (outlineProgress?.generated_episodes || []).includes(n)
      if (fromProgress || episodeHasContent(data)) nums.push(n)
    }
    return nums
  }, [episodeMap, outlineProgress, planned])

  const generated = generatedNums.length
  const progressPct = planned > 0 ? Math.min(100, Math.round((generated / planned) * 100)) : 0

  const [filter, setFilter] = useState('all')
  const [selectedNum, setSelectedNum] = useState(null)
  const [showStructure, setShowStructure] = useState(true)
  const [showForeshadow, setShowForeshadow] = useState(false)
  const [showRaw, setShowRaw] = useState(false)

  const episodes = useMemo(() => {
    const list = []
    for (let n = 1; n <= planned; n += 1) {
      const data = episodeMap.get(n)
      const isGenerated = generatedNums.includes(n)
      list.push({ num: n, generated: isGenerated, data: isGenerated ? data : null })
    }
    return list
  }, [planned, episodeMap, generatedNums])

  const filteredEpisodes = useMemo(() => {
    if (filter === 'done') return episodes.filter((e) => e.generated)
    if (filter === 'pending') return episodes.filter((e) => !e.generated)
    return episodes
  }, [episodes, filter])

  useEffect(() => {
    if (selectedNum && episodes.find((e) => e.num === selectedNum)) return
    const firstGenerated = generatedNums[0]
    const suggested = parseInt(String(outlineProgress?.suggested_range || '').split('-')[0], 10)
    if (firstGenerated) {
      setSelectedNum(firstGenerated)
    } else if (suggested) {
      setSelectedNum(suggested)
    } else {
      setSelectedNum(1)
    }
  }, [generatedNums, outlineProgress?.suggested_range, planned])

  const selectedEpisode = episodes.find((e) => e.num === selectedNum) || null
  const stages = viewBlock?.stages || []
  const foreshadowing = viewBlock?.foreshadowing || []
  const sixStageFromRaw = rawArtifact?.six_stage_structure
  const sixStageNarrative = rawArtifact?.six_stage_narrative
  const normalizedStages = useMemo(() => {
    if (stages.length) return stages
    const fromStruct = normalizeSixStage(sixStageFromRaw)
    if (fromStruct.length) return fromStruct
    if (Array.isArray(sixStageNarrative) && sixStageNarrative.length) {
      const idMap = { S1: 'opening', S2: 'warming', S3: 'climax', S4: 'turning', S5: 'sprint', S6: 'ending' }
      return sixStageNarrative.map((item, index) => ({
        key: idMap[String(item?.stage_id || '').toUpperCase()] || `stage-${index}`,
        index: index + 1,
        title: item?.stage_name || STAGE_LABELS[idMap[String(item?.stage_id || '').toUpperCase()]] || `阶段${index + 1}`,
        subtitle: item?.episode_range || '',
        summary: extractStageSummary(item),
      }))
    }
    return []
  }, [stages, sixStageFromRaw, sixStageNarrative])
  const hasStructureMeta = Boolean(
    sixStageFromRaw
    || (Array.isArray(sixStageNarrative) && sixStageNarrative.length)
    || rawArtifact?.rhythm_dual_track_validation,
  )
  const structureStageCount = normalizedStages.length
  const rawFormatted = formatPayloadText(rawArtifact)

  const handleRequestGenerate = (num) => {
    if (onSelectRange) onSelectRange(rangeForEpisode(num, batchSize, planned))
    setSelectedNum(num)
  }

  return (
    <div className="space-y-5">
      {/* 进度总览 */}
      <div className="rounded-2xl border border-gold-500/25 bg-gradient-to-br from-gold-500/10 via-navy-900/40 to-transparent p-5">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="flex items-center gap-4 flex-1">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-500/15 text-gold-400">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-300/80">全剧分集大纲</p>
              <p className="text-3xl font-bold tabular-nums text-white mt-0.5">
                {generated}
                <span className="text-lg text-slate-500 font-medium mx-1">/</span>
                {planned}
                <span className="text-sm text-slate-400 font-medium ml-1">集</span>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-1 text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              已生成 {generated}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/5 border border-white/10 px-2.5 py-1 text-slate-400">
              <span className="h-2 w-2 rounded-full bg-slate-600" />
              待生成 {planned - generated}
            </span>
            {outlineProgress?.suggested_range ? (
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/25 px-2.5 py-1 text-cyan-300">
                <Sparkles className="h-3 w-3" />
                建议下一批 {outlineProgress.suggested_range}
              </span>
            ) : null}
          </div>
        </div>
        <div className="mt-4 h-2.5 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-gold-500 via-amber-400 to-gold-300 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* 主区：地图 + 详情 */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)] gap-5">
        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Layers className="h-4 w-4 text-gold-400" />
              全剧分集地图
            </h4>
            <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-black/20 p-1">
              <Filter className="h-3.5 w-3.5 text-slate-500 ml-2" />
              {[
                { id: 'all', label: '全部' },
                { id: 'done', label: '已有' },
                { id: 'pending', label: '待生成' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setFilter(opt.id)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                    filter === opt.id
                      ? 'bg-gold-500/20 text-gold-300'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div
            className="grid gap-2"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(2.75rem, 1fr))' }}
          >
            {filteredEpisodes.map((ep) => {
              const isSelected = ep.num === selectedNum
              return (
                <button
                  key={`ep-cell-${ep.num}`}
                  type="button"
                  onClick={() => setSelectedNum(ep.num)}
                  title={ep.generated ? `第 ${ep.num} 集 · 已生成` : `第 ${ep.num} 集 · 待生成`}
                  className={`relative flex flex-col items-center justify-center rounded-xl border py-2.5 transition-all ${
                    isSelected
                      ? 'border-gold-500 bg-gold-500/20 ring-2 ring-gold-500/40 scale-105 z-10'
                      : ep.generated
                        ? 'border-emerald-500/40 bg-emerald-500/10 hover:border-emerald-400/60'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
                  }`}
                >
                  <span className={`text-sm font-bold tabular-nums ${ep.generated ? 'text-emerald-200' : 'text-slate-500'}`}>
                    {ep.num}
                  </span>
                  <span
                    className={`mt-1 h-1.5 w-1.5 rounded-full ${
                      ep.generated ? 'bg-emerald-400' : 'bg-slate-600'
                    }`}
                  />
                </button>
              )
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-4">
            点击集号查看详情；绿色为已生成，灰色为待生成。所有集数同时可见，不会因切换批次而隐藏。
          </p>
        </section>

        <section>
          <h4 className="text-sm font-semibold text-slate-200 mb-3">
            分集详情
            {selectedNum ? (
              <span className="text-gold-400 font-normal ml-2">· 第 {selectedNum} 集</span>
            ) : null}
          </h4>
          <EpisodeDetail
            episode={selectedEpisode}
            totalEpisodes={planned}
            onRequestGenerate={onSelectRange ? handleRequestGenerate : undefined}
          />
        </section>
      </div>

      {/* 附属：结构 / 伏笔 / JSON（在分集地图下方，需向下滚动） */}
      <div className="space-y-2">
        <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowStructure((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-300 hover:bg-white/[0.04]"
          >
            <span className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-gold-400" />
              六阶段叙事结构
              <span className={`text-xs font-normal ${structureStageCount ? 'text-emerald-400' : 'text-amber-400'}`}>
                {structureStageCount ? `${structureStageCount} 个阶段` : '未生成'}
              </span>
            </span>
            {showStructure ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {showStructure ? (
            structureStageCount > 0 ? (
              <div className="px-4 pb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {normalizedStages.map((stage) => (
                  <div
                    key={`stage-${stage.key || stage.index}`}
                    className="rounded-lg border border-white/10 bg-white/[0.03] p-3"
                  >
                    <p className="text-xs font-semibold text-gold-300">{stage.title}</p>
                    {stage.subtitle ? (
                      <p className="text-[11px] text-slate-500 mt-0.5">{stage.subtitle}</p>
                    ) : null}
                    {stage.summary ? (
                      <p className="text-xs text-slate-400 mt-2 leading-relaxed line-clamp-3">{stage.summary}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 pb-4 space-y-3">
                <p className="text-sm text-slate-400 leading-relaxed">
                  六阶段叙事结构、伏笔清单等全剧元数据只需生成一次，与分集批次无关。
                  {hasStructureMeta ? '当前结构字段为空或格式未识别。' : '当前项目尚未写入全剧结构。'}
                  {onGenerateStructure ? (
                    <> 可点击下方按钮单独补跑（不会覆盖已有分集大纲）。</>
                  ) : (
                    <> 分集大纲进度不受影响。</>
                  )}
                </p>
                {structureStageCount === 0 && onGenerateStructure ? (
                  <button
                    type="button"
                    onClick={onGenerateStructure}
                    disabled={structureLoading}
                    className="inline-flex items-center gap-2 rounded-xl border border-gold-500/50 bg-gold-500/15 px-4 py-2.5 text-sm font-semibold text-gold-200 hover:bg-gold-500/25 disabled:opacity-50"
                  >
                    {structureLoading ? '结构生成中…' : '生成全剧结构'}
                  </button>
                ) : null}
                <p className="text-xs text-slate-500">
                  也可展开下方「原始 JSON」，搜索
                  <code className="mx-1 rounded bg-black/30 px-1.5 py-0.5 text-slate-300">six_stage_structure</code>
                  或
                  <code className="mx-1 rounded bg-black/30 px-1.5 py-0.5 text-slate-300">six_stage_narrative</code>
                  查看是否已有数据。
                </p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {STAGE_ORDER.map((key) => (
                    <div
                      key={`stage-empty-${key}`}
                      className="rounded-lg border border-dashed border-white/15 bg-white/[0.02] p-3"
                    >
                      <p className="text-xs font-semibold text-slate-500">{STAGE_LABELS[key]}</p>
                      <p className="text-[11px] text-slate-600 mt-1">待生成</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          ) : null}
        </div>

        {foreshadowing.length > 0 ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <button
              type="button"
              onClick={() => setShowForeshadow((v) => !v)}
              className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-300 hover:bg-white/[0.04]"
            >
              <span>伏笔清单 ({foreshadowing.length})</span>
              {showForeshadow ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {showForeshadow ? (
              <div className="px-4 pb-4 grid gap-2 lg:grid-cols-2">
                {foreshadowing.map((item, i) => (
                  <div key={`fs-${i}`} className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
                    <div className="flex items-center gap-2 text-xs text-gold-400 mb-1">
                      {item.type ? <span>{item.type}</span> : null}
                      {item.buried != null && item.payoff != null ? (
                        <span className="text-slate-500">第{item.buried}集 → 第{item.payoff}集</span>
                      ) : null}
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{item.content}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowRaw((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-300 hover:bg-white/[0.04]"
          >
            <span>原始 JSON（聚合后全量）</span>
            {showRaw ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {showRaw && !rawFormatted.empty ? (
            <pre className="max-h-80 overflow-auto p-4 text-[11px] leading-relaxed text-slate-300 font-mono border-t border-white/10">
              {rawFormatted.text}
            </pre>
          ) : null}
        </div>
      </div>
    </div>
  )
}

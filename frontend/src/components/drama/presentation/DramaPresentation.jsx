import { useMemo, useState, useEffect } from 'react'
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clapperboard,
  Clock,
  FileText,
  Flame,
  Globe2,
  Heart,
  Lightbulb,
  Link2,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  XCircle,
  Zap,
} from 'lucide-react'
import { formatPayloadText } from '../../shared/PayloadInspector'

function SectionTitle({ children }) {
  return (
    <h5 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
      <span className="w-1 h-4 rounded-full bg-gold-500" />
      {children}
    </h5>
  )
}

function MetricsBlock({ block }) {
  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <div className={`grid grid-cols-2 sm:grid-cols-3 gap-3 ${block.title ? 'mt-3' : ''}`}>
        {(block.items || []).map((item, index) => (
          <div
            key={`${item.label}-${index}`}
            className="rounded-xl bg-gradient-to-br from-gold-500/10 to-white/[0.02] border border-gold-500/20 px-4 py-3 backdrop-blur-sm"
          >
            <p className="text-[11px] font-medium text-gold-300/90">{item.label}</p>
            <p className="text-xl font-bold text-white mt-1 tabular-nums">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function HeroBlock({ block }) {
  if (block.variant === 'brief') {
    return (
      <div className="rounded-2xl border border-gold-500/20 bg-gradient-to-br from-gold-500/10 via-navy-900/50 to-cyan-500/5 px-6 py-5 shadow-lg shadow-black/10 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-gold-400 shrink-0" />
          <p className="text-xs font-semibold tracking-wide text-gold-300">
            {block.title || '核心创意'}
          </p>
        </div>
        <p className="text-base sm:text-[17px] text-slate-100 leading-8 font-medium whitespace-pre-wrap">
          {block.subtitle}
        </p>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-gold-500/20 bg-gradient-to-br from-gold-500/8 via-navy-900/40 to-cyan-500/5 px-5 py-4 shadow-lg shadow-black/10 backdrop-blur-sm">
      <Sparkles className="absolute right-4 top-4 h-5 w-5 text-gold-500/30" />
      {block.title ? (
        <p className="text-xs font-semibold uppercase tracking-wide text-gold-300 mb-2">{block.title}</p>
      ) : null}
      {block.subtitle ? (
        <p className="text-[15px] text-slate-200 leading-7 whitespace-pre-wrap pr-8">{block.subtitle}</p>
      ) : null}
    </div>
  )
}

function KvBlock({ block }) {
  const rows = block.rows || []
  if (!rows.length) return null

  const isEmbedded = block.variant === 'embedded'
  const isTwoColumn = !isEmbedded && block.layout === 'columns_2'

  const rowList = (
    <dl
      className={
        isTwoColumn
          ? 'grid gap-3 p-4 sm:grid-cols-2'
          : isEmbedded
            ? 'divide-y divide-white/5'
            : 'divide-y divide-white/5'
      }
    >
      {rows.map((row, index) => {
        const isLong = String(row.value || '').length > 120
        const spanFull = isTwoColumn && isLong
        return (
          <div
            key={`${block.title || 'kv'}-${row.key}-${index}`}
            className={
              isTwoColumn
                ? `rounded-lg border border-white/10 bg-white/[0.03] px-4 py-3.5 hover:bg-white/[0.06] transition-colors ${
                    spanFull ? 'sm:col-span-2' : ''
                  }`
                : isEmbedded
                  ? `px-5 py-3.5 ${index > 0 ? 'border-t border-white/5' : ''}`
                  : `px-5 py-4 ${isLong ? 'bg-white/[0.02]' : 'hover:bg-white/[0.04]'} transition-colors`
            }
          >
            {isEmbedded ? (
              <div className="flex flex-col gap-1 sm:flex-row sm:gap-5">
                <dt className="sm:w-24 shrink-0 text-xs font-semibold text-slate-400">{row.key}</dt>
                <dd className="flex-1 min-w-0 text-sm text-slate-200 leading-7 whitespace-pre-wrap break-words">
                  {row.value}
                </dd>
              </div>
            ) : (
              <>
                <dt className="text-xs font-semibold text-gold-400 mb-2">{row.key}</dt>
                <dd
                  className={`text-sm text-slate-200 leading-7 whitespace-pre-wrap break-words ${
                    isLong ? 'pl-3 border-l-2 border-gold-500/30' : ''
                  }`}
                >
                  {row.value}
                </dd>
              </>
            )}
          </div>
        )
      })}
    </dl>
  )

  if (isEmbedded) {
    return rowList
  }

  return (
    <section className="w-full rounded-xl border border-white/10 overflow-hidden bg-white/[0.04] backdrop-blur-sm shadow-lg shadow-black/5">
      {block.title ? (
        <div className="px-5 py-3.5 bg-gradient-to-r from-white/[0.06] to-transparent border-b border-white/5">
          <SectionTitle>{block.title}</SectionTitle>
        </div>
      ) : null}
      {rowList}
    </section>
  )
}

function ParagraphBlock({ block }) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-4 backdrop-blur-sm">
      {block.title ? <div className="mb-2"><SectionTitle>{block.title}</SectionTitle></div> : null}
      <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap">{block.text}</p>
    </section>
  )
}

function ListBlock({ block }) {
  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <ul className={`space-y-2 ${block.title ? 'mt-3' : ''}`}>
        {(block.items || []).map((item, index) => (
          <li
            key={`${block.title}-${index}`}
            className="flex gap-2.5 text-sm text-slate-200 leading-relaxed"
          >
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-gold-400" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function CalloutBlock({ block }) {
  const isWarning = block.variant === 'warning'
  const isAccent = block.variant === 'accent'
  return (
    <section
      className={`rounded-xl border px-5 py-4 shadow-lg shadow-black/5 backdrop-blur-sm ${
        isWarning
          ? 'border-amber-500/20 bg-amber-500/10'
          : isAccent
            ? 'border-cyan-500/20 bg-cyan-500/10'
            : 'border-gold-500/20 bg-gold-500/8'
      }`}
    >
      {block.title ? (
        <div className="mb-2.5">
          <SectionTitle>{block.title}</SectionTitle>
        </div>
      ) : null}
      <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap">{block.text}</p>
    </section>
  )
}

function StepsBlock({ block }) {
  const isWarning = block.variant === 'warning'
  const badgeClass = isWarning ? 'bg-amber-500' : 'bg-gradient-to-r from-gold-500 to-gold-600'
  const cardClass = isWarning ? 'border-amber-500/20' : 'border-white/10'

  return (
    <section className="w-full">
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <ol className={`w-full list-none m-0 p-0 space-y-3 ${block.title ? 'mt-4' : ''}`}>
        {(block.items || []).map((item) => (
          <li
            key={`step-${item.index}-${item.title || item.body?.slice(0, 32) || 'body'}`}
            className="flex w-full min-w-0 gap-3 items-start"
          >
            <span
              className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white shadow-lg shadow-black/20 ${badgeClass}`}
            >
              {item.index}
            </span>
            <div
              className={`min-w-0 flex-1 basis-0 rounded-xl border bg-white/[0.04] px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur-sm ${cardClass}`}
            >
              {item.title ? (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-100 break-words">{item.title}</p>
                  {item.subtitle ? (
                    <span className="inline-block rounded-md bg-cyan-500/15 px-2 py-0.5 text-[11px] font-medium text-cyan-300 border border-cyan-500/20">
                      {item.subtitle}
                    </span>
                  ) : null}
                  {item.body ? (
                    <p className="text-sm text-slate-300 leading-7 whitespace-pre-wrap break-words">
                      {item.body}
                    </p>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap break-words">
                  {item.body}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}

const EMOTION_STYLES = {
  EV: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  ET: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  TP: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
}

function emotionKey(labelText) {
  if (labelText?.includes(' EV')) return 'EV'
  if (labelText?.includes(' ET')) return 'ET'
  if (labelText?.includes(' TP')) return 'TP'
  return null
}

function OutlineOverviewBlock({ block }) {
  const hasChecks = (block.checks || []).length > 0
  const hasReverses = (block.reverse_points || []).length > 0
  if (!block.total_episodes && !hasChecks && !hasReverses) return null

  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm shadow-lg shadow-black/5">
      <div className="grid divide-y lg:grid-cols-[auto_1fr] lg:divide-x lg:divide-y-0 divide-white/10">
        {block.total_episodes ? (
          <div className="flex items-center justify-center gap-4 bg-gradient-to-br from-gold-500/15 to-transparent px-6 py-5 lg:min-w-[150px]">
            <div className="text-center">
              <p className="text-[11px] font-medium uppercase tracking-wide text-gold-300/80">总集数</p>
              <p className="mt-1 text-4xl font-bold tabular-nums leading-none text-white">
                {block.total_episodes}
              </p>
            </div>
          </div>
        ) : null}

        <div className="min-w-0 divide-y divide-white/10">
          {hasChecks ? (
            <div className="space-y-3 px-5 py-4">
              <p className="text-xs font-semibold text-slate-400">节奏校验</p>
              {(block.checks || []).map((check, index) => (
                <div
                  key={`check-${index}`}
                  className="rounded-xl border border-emerald-500/20 bg-emerald-500/8 px-3.5 py-3"
                >
                  <p className="text-xs font-semibold text-emerald-300">{check.label}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-200 whitespace-pre-wrap break-words">
                    {check.text}
                  </p>
                </div>
              ))}
            </div>
          ) : null}

          {hasReverses ? (
            <div className="px-5 py-4">
              <p className="text-xs font-semibold text-slate-400 mb-2.5">A 级反转点</p>
              <div className="space-y-2">
                {(block.reverse_points || []).map((point, index) => (
                  <div
                    key={`reverse-${point.episode || index}`}
                    className="flex gap-3 rounded-lg bg-amber-500/8 border border-amber-500/20 px-3 py-2.5"
                  >
                    <span className="inline-flex shrink-0 items-center gap-1 rounded-md bg-amber-500/20 px-2 py-0.5 text-[11px] font-semibold text-amber-300 border border-amber-500/20">
                      <Zap className="h-3 w-3" />
                      {point.title}
                    </span>
                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap min-w-0">
                      {point.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

function EpisodeEmotionRow({ emotions }) {
  const items = (emotions || []).filter(Boolean)
  if (!items.length) return null

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, index) => {
        const key = emotionKey(item.label)
        const style = (key && EMOTION_STYLES[key]) || 'bg-white/[0.06] text-slate-300 border-white/10'
        return (
          <div
            key={`emotion-${index}`}
            className={`flex-1 min-w-[140px] rounded-lg border px-3 py-2 ${style}`}
          >
            <p className="text-[10px] font-bold uppercase tracking-wide opacity-80">{item.label}</p>
            <p className="mt-1 text-xs leading-relaxed whitespace-pre-wrap">{item.text}</p>
          </div>
        )
      })}
    </div>
  )
}

function EpisodeStructureTimeline({ structure }) {
  const items = (structure || []).filter(Boolean)
  if (!items.length) return null

  return (
    <ol className="relative space-y-0">
      {items.map((part, index) => (
        <li key={`part-${part.label}-${index}`} className="relative flex gap-3 pb-3 last:pb-0">
          <div className="flex flex-col items-center shrink-0 pt-1.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gold-500/20 text-[10px] font-bold text-gold-300 border border-gold-500/30">
              {index + 1}
            </span>
            {index < items.length - 1 ? (
              <span className="mt-1 w-px flex-1 min-h-[12px] bg-gold-500/20" aria-hidden />
            ) : null}
          </div>
          <div className="min-w-0 flex-1 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wide text-gold-400/90">{part.label}</p>
            <p className="mt-1 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap break-words">{part.text}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}

function EpisodeOutlineCard({ item, compact = false }) {
  if (item.missing) {
    return (
      <article className="rounded-xl border border-dashed border-white/15 bg-white/[0.02] px-4 py-5 text-center">
        <p className="text-sm font-medium text-slate-500">第 {item.episode_no} 集 · 待生成</p>
        <p className="text-xs text-slate-600 mt-1">在上方选择对应批次后执行情节架构师</p>
      </article>
    )
  }

  const structure = item.structure?.length ? item.structure : (item.sections || []).filter(
    (s) => !emotionKey(s.label),
  )
  const emotions = item.emotions?.length
    ? item.emotions
    : (item.sections || []).filter((s) => emotionKey(s.label))
  const episodeNo = item.episode_no || item.title?.match(/第(\d+)集/)?.[1]

  return (
    <article
      className={`rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden backdrop-blur-sm shadow-lg shadow-black/5 ${
        compact ? '' : ''
      }`}
    >
      <div className="flex gap-3 border-b border-white/10 bg-gradient-to-r from-white/[0.06] to-transparent px-4 py-3">
        {episodeNo ? (
          <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-gold-500 to-gold-600 text-white shadow-lg shadow-gold-500/20">
            <span className="text-[9px] font-medium uppercase leading-none opacity-80">EP</span>
            <span className="text-sm font-bold tabular-nums leading-none mt-0.5">{episodeNo}</span>
          </div>
        ) : null}
        <div className="min-w-0 flex-1">
          <h6 className="text-sm font-semibold text-slate-100 break-words">{item.title}</h6>
        </div>
      </div>

      <div className={compact ? 'px-3.5 py-3 space-y-3' : 'px-4 py-3.5 space-y-3'}>
        {item.subtitle ? (
          <blockquote className="rounded-lg border-l-[3px] border-amber-500/50 bg-amber-500/8 px-3 py-2.5 not-italic">
            <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-amber-300/90">
              集末钩子
            </span>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap break-words">{item.subtitle}</p>
          </blockquote>
        ) : null}

        {emotions.length > 0 ? (
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">情绪标记</p>
            <EpisodeEmotionRow emotions={emotions} />
          </div>
        ) : null}

        {structure.length > 0 ? (
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              {structure.some((s) => s.label === '目标与冲突' || s.label === '主题推进') ? '本集要点' : '四段结构'}
            </p>
            <EpisodeStructureTimeline structure={structure} />
          </div>
        ) : null}

        {(item.tags || []).filter(Boolean).length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {item.tags.filter(Boolean).map((tag, tagIndex) => (
              <span
                key={`${item.title}-tag-${tagIndex}`}
                className="rounded-md bg-gold-500/15 px-2 py-0.5 text-[11px] font-medium text-gold-300 border border-gold-500/20"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        {item.body ? (
          <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap break-words">{item.body}</p>
        ) : null}
      </div>
    </article>
  )
}

function StageOutlinesBlock({ block }) {
  const [expanded, setExpanded] = useState(() => new Set([block.stages?.[0]?.index].filter(Boolean)))

  const toggleStage = (index) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const expandAll = () => {
    setExpanded(new Set((block.stages || []).map((s) => s.index)))
  }

  const collapseAll = () => {
    setExpanded(new Set())
  }

  return (
    <section>
      <div className="flex items-center justify-between gap-3 mb-4">
        {block.title ? <SectionTitle>{block.title}</SectionTitle> : <span />}
        {(block.stages || []).length > 1 ? (
          <div className="flex gap-2 text-xs">
            <button
              type="button"
              onClick={expandAll}
              className="text-slate-400 hover:text-gold-400 transition-colors"
            >
              全部展开
            </button>
            <span className="text-slate-600">|</span>
            <button
              type="button"
              onClick={collapseAll}
              className="text-slate-400 hover:text-gold-400 transition-colors"
            >
              全部收起
            </button>
          </div>
        ) : null}
      </div>

      <div className="relative space-y-0">
        {(block.stages || []).map((stage, stageIndex) => {
          const isOpen = expanded.has(stage.index)
          const isLast = stageIndex === (block.stages || []).length - 1
          return (
            <div key={`stage-${stage.index}-${stage.title}`} className="relative flex gap-4">
              <div className="flex flex-col items-center shrink-0 w-8 pt-1">
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold shadow-lg shadow-black/10 ${
                    isOpen
                      ? 'bg-gradient-to-br from-gold-500 to-gold-600 text-white'
                      : 'bg-white/[0.08] text-gold-400 border-2 border-gold-500/30'
                  }`}
                >
                  {stage.index}
                </span>
                {!isLast ? (
                  <span className="w-px flex-1 min-h-[16px] bg-white/10 my-1" aria-hidden />
                ) : null}
              </div>

              <div className={`flex-1 min-w-0 ${isLast ? '' : 'pb-5'}`}>
                <div className="rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
                  <button
                    type="button"
                    onClick={() => toggleStage(stage.index)}
                    className="w-full flex items-start gap-3 px-4 py-3.5 text-left hover:bg-white/[0.06] transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-slate-100">{stage.title}</p>
                        {stage.subtitle ? (
                          <span className="rounded-full bg-white/[0.08] px-2.5 py-0.5 text-[11px] font-medium text-slate-300 border border-white/10">
                            {stage.subtitle}
                          </span>
                        ) : null}
                        <span className="text-xs text-slate-500">
                          {(stage.episodes || []).length} 集
                        </span>
                      </div>
                      {!isOpen && stage.summary ? (
                        <p className="mt-1.5 text-sm text-slate-400 leading-relaxed line-clamp-1">
                          {stage.summary}
                        </p>
                      ) : null}
                    </div>
                    {isOpen ? (
                      <ChevronUp className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                    )}
                  </button>

                  {isOpen ? (
                    <div className="px-4 pb-4 border-t border-white/10 space-y-4">
                      {(stage.summary || (stage.highlights || []).length > 0) ? (
                        <div className="pt-3 rounded-lg bg-white/[0.03] border border-white/10 px-3.5 py-3 space-y-3.5">
                          {stage.summary ? (
                            <div>
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-gold-400/90">
                                阶段说明
                              </p>
                              <p className="mt-1.5 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                                {stage.summary}
                              </p>
                            </div>
                          ) : null}

                          {(stage.highlights || []).length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-gold-400/90">
                                关键情节点
                              </p>
                              <ul className="mt-2 flex flex-wrap gap-2">
                                {stage.highlights.map((point, pointIndex) => (
                                  <li
                                    key={`stage-${stage.index}-point-${pointIndex}`}
                                    className="rounded-lg bg-white/[0.06] border border-white/10 px-3 py-1.5 text-xs text-slate-200 leading-relaxed max-w-full"
                                  >
                                    {point}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                        </div>
                      ) : null}

                      {(stage.episodes || []).length > 0 ? (
                        <div className="space-y-2.5">
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                            分集详情
                          </p>
                          {stage.episodes.map((episode, episodeIndex) => (
                            <EpisodeOutlineCard
                              key={`${stage.index}-ep-${episode.episode_no || episode.title}-${episodeIndex}`}
                              item={episode}
                              compact
                            />
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function BriefProfileCard({ item }) {
  return (
    <article className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-4 shadow-lg shadow-black/5 backdrop-blur-sm h-full flex flex-col min-w-0">
      <p className="text-xs font-semibold text-gold-400 mb-2.5 break-words">{item.title}</p>
      <p className="text-sm text-slate-300 leading-7 whitespace-pre-wrap break-words flex-1">{item.body}</p>
    </article>
  )
}

function characterInitial(name) {
  const text = String(name || '').trim()
  if (!text) return '?'
  return text.charAt(0)
}

function parseRelationshipNames(item) {
  if (item.source_name && item.target_name) {
    return { source: item.source_name, target: item.target_name }
  }
  const parts = String(item.title || '').split(/\s*↔\s*/)
  if (parts.length >= 2) {
    return { source: parts[0].trim(), target: parts[1].trim() }
  }
  return { source: item.title || '角色 A', target: '' }
}

function roleBadgeClass(roleLabel) {
  const text = String(roleLabel || '')
  if (/反派|对立|死敌|BOSS|敌人|督军|观测者/.test(text)) {
    return 'bg-rose-500/10 text-rose-300 border-rose-500/20'
  }
  if (/配角|配角|辅助|战友|老兵/.test(text)) {
    return 'bg-sky-500/10 text-sky-300 border-sky-500/20'
  }
  if (/女主|男主|主角|核心/.test(text)) {
    return 'bg-gold-500/10 text-gold-300 border-gold-500/20'
  }
  return 'bg-white/[0.06] text-slate-300 border-white/10'
}

function CharacterNode({ name }) {
  if (!name) return null
  return (
    <div className="flex min-w-0 flex-1 flex-col items-center gap-2">
      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-gold-500/30 bg-gradient-to-br from-gold-500/20 to-cyan-500/10 text-lg font-bold text-gold-300 shadow-lg shadow-black/10">
        {characterInitial(name)}
      </div>
      <p className="max-w-[130px] text-center text-sm font-semibold leading-snug text-slate-100 break-words">
        {name}
      </p>
    </div>
  )
}

function RelationshipCard({ item }) {
  const { source, target } = parseRelationshipNames(item)
  const relType = item.relationship_type || item.subtitle || ''
  const coreConflict = item.core_conflict || (!item.interaction_rule ? item.body : '')
  const interactionRule = item.interaction_rule || ''

  return (
    <article className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm shadow-lg shadow-black/5">
      <div className="border-b border-white/10 bg-gradient-to-r from-white/[0.06] via-transparent to-cyan-500/5 px-5 py-5">
        <div className="flex items-center justify-center gap-4 sm:gap-8">
          <CharacterNode name={source} />
          <div className="flex shrink-0 flex-col items-center gap-2 px-1">
            <div className="flex items-center gap-1 text-gold-400/50">
              <span className="h-px w-6 bg-gold-500/30" />
              <Link2 className="h-4 w-4 shrink-0" />
              <span className="h-px w-6 bg-gold-500/30" />
            </div>
            {relType ? (
              <span className="max-w-[150px] rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-center text-xs font-semibold leading-snug text-cyan-300">
                {relType}
              </span>
            ) : (
              <span className="text-[11px] text-slate-500">人物关系</span>
            )}
          </div>
          <CharacterNode name={target} />
        </div>
      </div>

      {coreConflict || interactionRule ? (
        <div className="space-y-4 px-5 py-4">
          {coreConflict ? (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 px-4 py-3.5">
              <p className="mb-1.5 text-[11px] font-semibold tracking-wide text-amber-300">核心冲突</p>
              <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{coreConflict}</p>
            </div>
          ) : null}
          {interactionRule ? (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3.5">
              <p className="mb-1.5 text-[11px] font-semibold tracking-wide text-slate-400">互动规则</p>
              <p className="text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{interactionRule}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

function CardsBlock({ block }) {
  const isStack = block.layout === 'stack'
  const isProfileGrid = block.variant === 'profile'
  const gridClass = block.layout === 'grid_3'
    ? 'grid-cols-1 lg:grid-cols-3'
    : block.layout === 'grid_2'
      ? 'grid-cols-1 md:grid-cols-2'
      : isStack
        ? 'grid-cols-1'
        : 'sm:grid-cols-2'

  if (isProfileGrid) {
    return (
      <section>
        {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
        <div className={`grid gap-4 ${gridClass} ${block.title ? 'mt-4' : ''}`}>
          {(block.items || []).map((item, index) => (
            <BriefProfileCard key={`${item.title}-${index}`} item={item} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <div className={`grid gap-3 ${isStack ? 'grid-cols-1' : 'sm:grid-cols-2'} ${block.title ? 'mt-3' : ''}`}>
        {(block.items || []).map((item, index) => (
          <EpisodeOutlineCard key={`${item.title}-${index}`} item={item} />
        ))}
      </div>
    </section>
  )
}

const REVIEW_ISSUE_STYLES = {
  格式问题: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  逻辑冗余: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
  结构问题: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  逻辑问题: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
}

function reviewIssueStyle(issueType) {
  return REVIEW_ISSUE_STYLES[issueType] || 'bg-white/[0.06] text-slate-300 border-white/10'
}

function ReviewOverviewBlock({ block }) {
  const passed = block.passed
  const pacingPassed = block.pacing_passed
  const issueCount = block.issue_count ?? 0

  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
      <div
        className={`px-4 py-4 border-b border-white/10 ${
          passed === false ? 'bg-red-500/10' : 'bg-emerald-500/10'
        }`}
      >
        <div className="flex items-center gap-2">
          {passed === false ? (
            <XCircle className="h-5 w-5 text-red-400" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          )}
          <span
            className={`text-sm font-semibold ${
              passed === false ? 'text-red-300' : 'text-emerald-300'
            }`}
          >
            {passed === false ? '审查未通过' : passed === true ? '审查通过' : '审稿结论'}
          </span>
          {issueCount > 0 ? (
            <span className="rounded-full bg-white/10 border border-white/10 px-2 py-0.5 text-[11px] text-slate-300">
              {issueCount} 项问题
            </span>
          ) : null}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/10">
        {passed !== null && passed !== undefined ? (
          <div className="flex items-center gap-3 px-4 py-3.5">
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                passed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
              }`}
            >
              {passed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            </span>
            <div>
              <p className="text-xs text-slate-500">整体结论</p>
              <p className="text-sm font-medium text-slate-200">{passed ? '通过' : '未通过'}</p>
            </div>
          </div>
        ) : null}

        {pacingPassed !== null && pacingPassed !== undefined ? (
          <div className="flex items-center gap-3 px-4 py-3.5">
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                pacingPassed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
              }`}
            >
              {pacingPassed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            </span>
            <div>
              <p className="text-xs text-slate-500">节奏检查</p>
              <p className="text-sm font-medium text-slate-200">{pacingPassed ? '通过' : '未通过'}</p>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  )
}

function ReviewIssuesBlock({ block }) {
  const items = block.items || []
  if (!items.length) return null

  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <div className={`space-y-2.5 ${block.title ? 'mt-3' : ''}`}>
        {items.map((item, index) => (
          <article
            key={`review-issue-${index}`}
            className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur-sm"
          >
            <div className="flex flex-wrap items-center gap-2 mb-2">
              {item.issue_type ? (
                <span
                  className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${reviewIssueStyle(item.issue_type)}`}
                >
                  {item.issue_type}
                </span>
              ) : null}
              {item.episode_number ? (
                <span className="rounded-full bg-gold-500/15 px-2 py-0.5 text-[11px] font-medium text-gold-300 border border-gold-500/20">
                  第{item.episode_number}集
                </span>
              ) : null}
              {item.scene_number ? (
                <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-white/10 tabular-nums">
                  {item.scene_number}
                </span>
              ) : null}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap flex gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
              <span>{item.description}</span>
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}

function VerdictBlock({ block }) {
  return (
    <section
      className={`rounded-xl border p-4 ${
        block.passed
          ? 'border-emerald-500/20 bg-emerald-500/10'
          : 'border-red-500/20 bg-red-500/10'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
        ) : (
          <XCircle className="h-5 w-5 text-red-400" />
        )}
        <span className={`text-sm font-semibold ${block.passed ? 'text-emerald-300' : 'text-red-300'}`}>
          {block.detail || (block.passed ? '通过' : '未通过')}
        </span>
      </div>
      {(block.issues || []).length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {block.issues.map((issue, index) => (
            <li key={`issue-${index}`} className="rounded-lg bg-white/[0.08] border border-white/10 px-3 py-2 text-sm text-slate-300 leading-relaxed">
              {issue}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}

function ComplianceReportBlock({ block }) {
  const levels = block.levels || []
  const nine = block.nine_dimension

  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
      <div
        className={`px-4 py-4 border-b border-white/10 ${
          block.passed ? 'bg-emerald-500/10' : 'bg-red-500/10'
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          {block.passed ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          ) : (
            <XCircle className="h-5 w-5 text-red-400" />
          )}
          <span
            className={`text-sm font-semibold ${
              block.passed ? 'text-emerald-300' : 'text-red-300'
            }`}
          >
            {block.passed ? '合规通过' : '合规未通过'}
          </span>
        </div>
        {block.conclusion ? (
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-7">
            {block.conclusion}
          </p>
        ) : null}
      </div>

      {levels.length > 0 ? (
        <div className="p-4 border-b border-white/10">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-3">
            三级风险扫描
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {levels.map((level) => (
              <article
                key={level.level}
                className={`rounded-xl border px-3.5 py-3 ${
                  level.passed
                    ? 'border-emerald-500/20 bg-emerald-500/8'
                    : 'border-amber-500/20 bg-amber-500/8'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className="text-sm font-semibold text-slate-100">{level.level}</p>
                  <span
                    className={`text-[11px] font-medium ${
                      level.passed ? 'text-emerald-300' : 'text-amber-300'
                    }`}
                  >
                    {level.status}
                  </span>
                </div>
                {level.detail ? (
                  <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap mt-1">
                    {level.detail}
                  </p>
                ) : null}
                {(level.items || []).length > 0 ? (
                  <ul className="mt-2 space-y-1.5">
                    {level.items.map((item, index) => (
                      <li
                        key={`${level.level}-risk-${index}`}
                        className="rounded-lg bg-white/[0.06] border border-white/10 px-2.5 py-2 text-xs text-slate-300 leading-relaxed"
                      >
                        {item.location ? (
                          <span className="font-medium text-slate-400 mr-1">{item.location}</span>
                        ) : null}
                        {item.description}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>
        </div>
      ) : null}

      {nine ? (
        <div className="p-4">
          <div className="flex items-center justify-between gap-2 mb-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              九维风险扫描
            </p>
            <span
              className={`text-[11px] font-medium ${
                nine.passed ? 'text-emerald-300' : 'text-amber-300'
              }`}
            >
              {nine.passed ? '通过' : '需关注'}
            </span>
          </div>

          {(nine.dimensions || []).length > 0 ? (
            <div className="grid gap-2 sm:grid-cols-3 mb-3">
              {nine.dimensions.map((dim, index) => (
                <div
                  key={`${dim.name}-${index}`}
                  className={`rounded-lg border px-3 py-2 text-xs ${
                    dim.passed
                      ? 'border-emerald-500/20 bg-emerald-500/8 text-emerald-300'
                      : 'border-amber-500/20 bg-amber-500/8 text-amber-300'
                  }`}
                >
                  <p className="font-medium">{dim.name}</p>
                  <p className="mt-0.5 opacity-80">{dim.status}</p>
                </div>
              ))}
            </div>
          ) : null}

          {nine.summary ? (
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap mb-2">
              {nine.summary}
            </p>
          ) : null}

          {(nine.items || []).length === 0 && !(nine.dimensions || []).length && !nine.summary ? (
            <p className="text-sm text-slate-500">未发现风险项</p>
          ) : null}

          {(nine.items || []).length > 0 ? (
            <ul className="space-y-2">
              {nine.items.map((item, index) => (
                <li
                  key={`nine-risk-${index}`}
                  className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300 leading-relaxed"
                >
                  {item.description}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}

function QualityReportBlock({ block }) {
  const dimensions = block.dimensions || []
  const total = block.total_score
  const maxTotal = block.max_total ?? 100
  const rating = block.rating
  const fuseTriggered = block.fuse_triggered

  const ratingStyle =
    rating === 'S'
      ? 'from-amber-400 to-yellow-500 text-navy-950'
      : rating === 'A'
        ? 'from-gold-400 to-gold-600 text-navy-950'
        : 'from-slate-500 to-slate-600 text-white'

  const totalPercent =
    total != null && maxTotal ? Math.min(100, Math.round((Number(total) / maxTotal) * 100)) : null

  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
      <div className="px-5 py-5 bg-gradient-to-br from-white/[0.06] via-transparent to-gold-500/5 border-b border-white/10">
        <div className="flex flex-wrap items-end gap-4">
          {rating ? (
            <span
              className={`inline-flex h-14 min-w-[3.5rem] items-center justify-center rounded-2xl bg-gradient-to-br px-4 text-3xl font-black shadow-lg shadow-black/20 ${ratingStyle}`}
            >
              {rating}
            </span>
          ) : null}
          <div>
            {total != null ? (
              <p className="text-2xl font-bold text-white tabular-nums leading-none">
                {total}
                <span className="text-base font-medium text-slate-400"> / {maxTotal}</span>
              </p>
            ) : null}
            {totalPercent != null ? (
              <p className="mt-1 text-xs text-slate-500">综合得分 {totalPercent}%</p>
            ) : null}
          </div>
          {fuseTriggered === true ? (
            <span className="ml-auto rounded-lg border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-300">
              已触发熔断
            </span>
          ) : fuseTriggered === false ? (
            <span className="ml-auto rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
              未触发熔断
            </span>
          ) : null}
        </div>
      </div>

      {dimensions.length > 0 ? (
        <div className="p-4 space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 px-1">
            维度评分
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {dimensions.map((row, index) => {
              const scoreNum = Number(row.score)
              const maxScore = row.max_score != null ? Number(row.max_score) : null
              const percent =
                maxScore && !Number.isNaN(scoreNum)
                  ? Math.min(100, Math.round((scoreNum / maxScore) * 100))
                  : null
              const barColor =
                percent == null ? 'bg-gold-500' : percent >= 90 ? 'bg-emerald-500' : percent >= 75 ? 'bg-gold-500' : 'bg-amber-500'

              return (
                <article
                  key={`${row.name}-${index}`}
                  className="rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-3"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <p className="text-sm font-medium text-slate-200">{row.name}</p>
                    <p className="text-sm font-bold text-white tabular-nums shrink-0">
                      {row.score}
                      {maxScore != null ? (
                        <span className="text-xs font-medium text-slate-400"> / {maxScore}</span>
                      ) : null}
                    </p>
                  </div>
                  {percent != null ? (
                    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden mb-2">
                      <div
                        className={`h-full rounded-full transition-all ${barColor}`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  ) : null}
                  {row.detail ? (
                    <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap">
                      {row.detail}
                    </p>
                  ) : null}
                </article>
              )
            })}
          </div>
        </div>
      ) : null}
    </section>
  )
}

function parseScoreMeta(rawScore) {
  const text = String(rawScore ?? '').trim()
  if (!text) return null
  const fraction = text.match(/^([\d.]+)\s*\/\s*([\d.]+)$/)
  if (fraction) {
    const num = Number(fraction[1])
    const max = Number(fraction[2])
    if (!Number.isNaN(num) && !Number.isNaN(max) && max > 0) {
      return { num, max, percent: Math.min(100, Math.round((num / max) * 100)) }
    }
  }
  const num = Number(text)
  if (Number.isNaN(num)) return null
  const max = num <= 5 ? 5 : num <= 10 ? 10 : 100
  return { num, max, percent: Math.min(100, Math.round((num / max) * 100)) }
}

function scoreBarColor(percent) {
  if (percent >= 90) return 'bg-emerald-400'
  if (percent >= 75) return 'bg-gold-400'
  if (percent >= 60) return 'bg-cyan-400'
  return 'bg-amber-400'
}

function gradeBadgeStyle(grade) {
  const g = String(grade || '').toUpperCase()
  if (g === 'S') return 'from-amber-300 via-yellow-400 to-orange-400 text-navy-950 shadow-amber-500/30'
  if (g === 'A') return 'from-gold-400 via-gold-500 to-amber-500 text-navy-950 shadow-gold-500/30'
  if (g === 'B') return 'from-cyan-400 to-cyan-600 text-navy-950 shadow-cyan-500/20'
  return 'from-slate-400 to-slate-600 text-white shadow-slate-500/20'
}

function ScoreBoardBlock({ block }) {
  const dimensions = block.dimensions || []
  const totalMeta = parseScoreMeta(block.total)
  const grade = block.grade

  return (
    <section className="relative overflow-hidden rounded-2xl border border-gold-500/20 bg-gradient-to-br from-navy-900/90 via-navy-950/95 to-gold-950/30 shadow-xl shadow-black/20">
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-gold-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-10 h-40 w-40 rounded-full bg-cyan-500/8 blur-3xl" />

      <div className="relative border-b border-white/10 px-6 py-6">
        <div className="flex flex-wrap items-end gap-5">
          {grade ? (
            <div
              className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-3xl font-black shadow-lg ${gradeBadgeStyle(grade)}`}
            >
              {grade}
            </div>
          ) : null}
          <div className="min-w-0 flex-1">
            {block.title ? (
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-300/80">
                {block.title}
              </p>
            ) : null}
            {totalMeta ? (
              <p className="mt-1 text-3xl font-bold tabular-nums leading-none text-white">
                {totalMeta.num}
                <span className="ml-1 text-lg font-medium text-slate-400">/ {totalMeta.max}</span>
              </p>
            ) : block.total != null ? (
              <p className="mt-1 text-3xl font-bold tabular-nums text-white">{block.total}</p>
            ) : null}
            {totalMeta ? (
              <p className="mt-2 text-xs text-slate-400">综合得分 {totalMeta.percent}%</p>
            ) : null}
          </div>
          {totalMeta ? (
            <div className="relative h-14 w-14 shrink-0">
              <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36" aria-hidden>
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="3" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke="url(#marketScoreGradient)"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={`${totalMeta.percent} 100`}
                />
                <defs>
                  <linearGradient id="marketScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#fbbf24" />
                    <stop offset="100%" stopColor="#22d3ee" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-gold-300">
                {totalMeta.percent}%
              </span>
            </div>
          ) : null}
        </div>
        {block.summary ? (
          <p className="mt-4 text-sm leading-relaxed text-slate-300 border-l-2 border-gold-500/40 pl-3">
            {block.summary}
          </p>
        ) : null}
      </div>

      {dimensions.length > 0 ? (
        <div className="relative p-5">
          <p className="mb-4 px-1 text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-500">
            维度细项
          </p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {dimensions.map((row, index) => {
              const meta = parseScoreMeta(row.score)
              const percent = meta?.percent ?? null
              return (
                <article
                  key={`${row.name}-${index}`}
                  className="group rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 transition-colors hover:border-gold-500/25 hover:bg-white/[0.06]"
                >
                  <div className="mb-2.5 flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-slate-200">{row.name}</p>
                    <p className="shrink-0 text-sm font-bold tabular-nums text-white">
                      {row.score}
                      {meta ? <span className="text-xs font-medium text-slate-500"> / {meta.max}</span> : null}
                    </p>
                  </div>
                  {percent != null ? (
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                      <div
                        className={`h-full rounded-full transition-all ${scoreBarColor(percent)}`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  ) : null}
                </article>
              )
            })}
          </div>
        </div>
      ) : null}
    </section>
  )
}

function ChecksBlock({ block }) {
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.04] p-4 shadow-lg shadow-black/5 backdrop-blur-sm space-y-3">
      <div className="flex items-center gap-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
        ) : (
          <XCircle className="h-5 w-5 text-red-400" />
        )}
        <span className="text-sm font-semibold text-slate-100">{block.verdict || '—'}</span>
      </div>
      <div className="space-y-2">
        {(block.items || []).map((row, index) => (
          <div key={`${row.level}-${index}`} className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5">
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="font-medium text-slate-200">{row.level}</span>
              <span className="text-xs font-medium text-slate-400">{row.status}</span>
            </div>
            {row.detail ? (
              <p className="mt-1.5 text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">{row.detail}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

function parseDialogueLine(line) {
  if (!line) return null
  const toneMatch = line.match(/^(.+?)（(.+)）[：:]([\s\S]+)$/)
  if (toneMatch) {
    return { speaker: toneMatch[1].trim(), tone: toneMatch[2].trim(), text: toneMatch[3].trim() }
  }
  const simpleMatch = line.match(/^(.+?)[：:]([\s\S]+)$/)
  if (simpleMatch) {
    return { speaker: simpleMatch[1].trim(), tone: '', text: simpleMatch[2].trim() }
  }
  return null
}

function parseSceneHeader(header) {
  if (!header) return { sceneId: '', location: '' }
  const match = header.match(/^(\d+-\d+)\s*(.*)$/)
  if (match) {
    return { sceneId: match[1], location: match[2].trim() || header }
  }
  return { sceneId: '', location: header }
}

function ScriptSceneBeat({ beat, showHeader = true }) {
  const { sceneId, location } = parseSceneHeader(beat.sceneHeader)
  const dialogue = parseDialogueLine(beat.dialogue)

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] overflow-hidden backdrop-blur-sm">
      {showHeader && beat.sceneHeader ? (
        <div className="flex flex-wrap items-center gap-2 px-3 py-2 bg-white/[0.04] border-b border-white/10">
          {sceneId ? (
            <span className="rounded-md bg-gradient-to-r from-gold-500 to-gold-600 px-2 py-0.5 text-[11px] font-bold text-navy-950 tabular-nums shadow-gold">
              {sceneId}
            </span>
          ) : null}
          <span className="text-xs font-medium text-gold-300">{location || beat.sceneHeader}</span>
        </div>
      ) : null}

      <div className="px-3 py-2.5 space-y-2">
        {beat.action ? (
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
            {beat.action}
          </p>
        ) : null}

        {dialogue ? (
          <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/8 px-3 py-2.5">
            <p className="text-sm leading-relaxed text-slate-100">
              <span className="font-semibold text-cyan-300">{dialogue.speaker}</span>
              {dialogue.tone ? (
                <span className="text-xs text-cyan-400/90 ml-1">（{dialogue.tone}）</span>
              ) : null}
              <span className="text-slate-500 mx-1">：</span>
              <span>{dialogue.text}</span>
            </p>
          </div>
        ) : beat.dialogue ? (
          <p className="rounded-lg border border-cyan-500/20 bg-cyan-500/8 px-3 py-2.5 text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">
            {beat.dialogue}
          </p>
        ) : null}
      </div>
    </div>
  )
}

function ScriptEpisodesBlock({ block }) {
  const episodes = block.episodes || []
  const [expanded, setExpanded] = useState(() => new Set([episodes[0]?.episodeNumber].filter(Boolean)))
  const [activeEp, setActiveEp] = useState(episodes[0]?.episodeNumber ?? null)

  const toggleEpisode = (epNo) => {
    setActiveEp(epNo)
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(epNo)) {
        next.delete(epNo)
      } else {
        next.add(epNo)
      }
      return next
    })
  }

  const expandAll = () => {
    setExpanded(new Set(episodes.map((ep) => ep.episodeNumber)))
  }

  const collapseAll = () => {
    setExpanded(new Set())
  }

  const totalScenes = useMemo(
    () => episodes.reduce((sum, ep) => sum + (ep.sceneCount || ep.beats?.filter((b) => b.sceneHeader)?.length || 0), 0),
    [episodes],
  )

  if (!episodes.length) return null

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur-sm flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold-500/15 text-gold-400">
            <BookOpen className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-medium text-slate-500">剧本规模</p>
            <p className="text-sm font-semibold text-slate-100 tabular-nums">
              {block.total_episodes ?? episodes.length} 集 · {totalScenes} 场
            </p>
          </div>
        </div>
        {episodes.length > 1 ? (
          <div className="flex gap-2 text-xs ml-auto">
            <button type="button" onClick={expandAll} className="text-slate-400 hover:text-gold-400 transition-colors">
              全部展开
            </button>
            <span className="text-slate-600">|</span>
            <button type="button" onClick={collapseAll} className="text-slate-400 hover:text-gold-400 transition-colors">
              全部收起
            </button>
          </div>
        ) : null}
      </div>

      {episodes.length > 3 ? (
        <div className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2.5 shadow-lg shadow-black/5 backdrop-blur-sm">
          <p className="text-[11px] font-medium text-slate-500 mb-2 px-1">快速跳转</p>
          <div className="flex gap-1.5 overflow-x-auto pb-0.5">
            {episodes.map((ep) => (
              <button
                key={`nav-${ep.episodeNumber}`}
                type="button"
                onClick={() => {
                  setActiveEp(ep.episodeNumber)
                  setExpanded((prev) => new Set(prev).add(ep.episodeNumber))
                  document.getElementById(`script-ep-${ep.episodeNumber}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}
                className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  activeEp === ep.episodeNumber
                    ? 'bg-gradient-to-r from-gold-500 to-gold-600 text-navy-950 shadow-gold'
                    : 'bg-white/[0.08] text-slate-300 hover:bg-white/[0.15] border border-white/10'
                }`}
              >
                第{ep.episodeNumber}集
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="space-y-3">
        {episodes.map((episode) => {
          const epNo = episode.episodeNumber
          const isOpen = expanded.has(epNo)
          const isActive = activeEp === epNo
          const sceneCount = episode.sceneCount || episode.beats?.filter((b) => b.sceneHeader)?.length || 0
          const visibleBeats = (episode.beats || []).filter((b) => b.sceneHeader || b.action || b.dialogue)

          return (
            <article
              key={epNo}
              id={`script-ep-${epNo}`}
              className={`rounded-xl border bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm scroll-mt-4 transition-colors ${
                isActive ? 'border-gold-500/30 ring-1 ring-gold-500/10' : 'border-white/10'
              }`}
            >
              <button
                type="button"
                onClick={() => toggleEpisode(epNo)}
                className="w-full flex items-center gap-3 px-4 py-3.5 text-left hover:bg-white/[0.06] transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-slate-100">
                      第{epNo}集
                      {episode.title && episode.title !== `第${epNo}集` ? ` · ${episode.title}` : ''}
                    </p>
                    {sceneCount > 0 ? (
                      <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-[11px] text-slate-400 border border-white/10">
                        {sceneCount} 场
                      </span>
                    ) : null}
                  </div>
                  {!isOpen && episode.memoryCheckPoint ? (
                    <p className="mt-1 text-xs text-slate-500 line-clamp-1">{episode.memoryCheckPoint}</p>
                  ) : null}
                </div>
                {isOpen ? (
                  <ChevronUp className="h-4 w-4 text-slate-400 shrink-0" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                )}
              </button>

              {isOpen ? (
                <div className="px-4 pb-4 border-t border-white/10 space-y-3">
                  {episode.memoryCheckPoint ? (
                    <div className="pt-3 rounded-lg bg-emerald-500/8 border border-emerald-500/20 px-3.5 py-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-300/90">
                        记忆检查点
                      </p>
                      <p className="mt-1.5 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                        {episode.memoryCheckPoint}
                      </p>
                    </div>
                  ) : null}

                  {visibleBeats.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                        场次剧本
                      </p>
                      {visibleBeats.map((beat, index) => {
                        const prev = visibleBeats[index - 1]
                        const showHeader = Boolean(
                          beat.sceneHeader && beat.sceneHeader !== prev?.sceneHeader,
                        )
                        return (
                          <ScriptSceneBeat
                            key={`${epNo}-beat-${index}`}
                            beat={beat}
                            showHeader={showHeader}
                          />
                        )
                      })}
                    </div>
                  ) : (
                    <p className="pt-3 text-sm text-slate-500 text-center py-6">暂无场次内容</p>
                  )}
                </div>
              ) : null}
            </article>
          )
        })}
      </div>
    </section>
  )
}

function PlanOverviewBlock({ block }) {
  const hasMetrics = (block.metrics || []).length > 0
  const hasChecks = (block.checks || []).length > 0
  if (!block.hero_text && !hasMetrics && !hasChecks) return null
  return (
    <section className="rounded-xl border border-gold-500/20 bg-gradient-to-br from-gold-500/8 via-navy-900/40 to-cyan-500/5 overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
      {block.title ? (
        <div className="px-5 py-3 border-b border-gold-500/20">
          <SectionTitle>{block.title}</SectionTitle>
        </div>
      ) : null}
      <div className="p-5 space-y-4">
        {block.hero_text ? (
          <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap">{block.hero_text}</p>
        ) : null}
        {hasMetrics ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {block.metrics.map((item, index) => (
              <div key={`${item.label}-${index}`} className="rounded-lg bg-white/[0.06] border border-white/10 px-3 py-2.5 backdrop-blur-sm">
                <p className="text-[11px] text-gold-400">{item.label}</p>
                <p className="text-lg font-bold text-white mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        ) : null}
        {hasChecks ? (
          <div className="space-y-2">
            {block.checks.map((check, index) => (
              <div key={`check-${index}`} className="rounded-lg bg-white/[0.04] border border-white/10 px-3.5 py-3">
                <p className="text-xs font-semibold text-slate-400">{check.label}</p>
                <p className="mt-1 text-sm text-slate-200 leading-relaxed">{check.text}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

function PlanItemsBlock({ block }) {
  const items = block.items || []
  if (!items.length) return null
  return <CardsBlock block={{ title: block.title, items }} />
}

function CharacterRosterBlock({ block }) {
  const characters = block.characters || []
  if (!characters.length) return null
  return (
    <section className="w-full space-y-4">
      <SectionTitle>角色档案</SectionTitle>
      {characters.map((char, index) => (
        <article
          key={`char-${char.badge || char.title}-${index}`}
          className="w-full min-w-0 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] shadow-lg shadow-black/5 backdrop-blur-sm"
        >
          <header className="flex flex-wrap items-center gap-2 border-b border-white/10 bg-gradient-to-r from-white/[0.06] to-transparent px-5 py-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-gold-500/30 bg-gold-500/15 text-sm font-bold text-gold-300">
              {characterInitial(char.title)}
            </div>
            <div className="min-w-0 flex-1">
              <h6 className="text-base font-semibold text-slate-100 break-words">{char.title}</h6>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                {char.role_label ? (
                  <span
                    className={`rounded-md border px-2 py-0.5 text-[11px] font-medium ${roleBadgeClass(char.role_label)}`}
                  >
                    {char.role_label}
                  </span>
                ) : null}
                {char.badge ? (
                  <span className="rounded-md bg-white/[0.08] px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-white/10">
                    {char.badge}
                  </span>
                ) : null}
              </div>
            </div>
          </header>
          {(char.rows || []).length ? (
            <KvBlock block={{ rows: char.rows || [], variant: 'embedded' }} />
          ) : null}
        </article>
      ))}
    </section>
  )
}

function RelationshipGraphBlock({ block }) {
  const items = block.items || []
  if (!items.length) return null
  return (
    <section className="w-full space-y-4">
      <div>
        <SectionTitle>
          <span className="inline-flex items-center gap-2">
            <Users className="h-4 w-4 text-gold-400" />
            人物关系网络
          </span>
        </SectionTitle>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          展示角色之间的定位关系与剧情冲突，便于快速把握人物对立与联盟。
        </p>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {items.map((item, index) => (
          <RelationshipCard key={`rel-${item.source_name || item.title}-${index}`} item={item} />
        ))}
      </div>
    </section>
  )
}

const MARKET_SECTION_STYLES = {
  indigo: {
    icon: TrendingUp,
    accent: 'text-gold-400',
    ring: 'ring-gold-500/20',
    header: 'from-gold-500/12 via-gold-500/5 to-transparent',
    border: 'border-gold-500/20',
    iconBg: 'bg-gold-500/15 text-gold-400',
    dot: 'bg-gold-400',
  },
  violet: {
    icon: Target,
    accent: 'text-cyan-400',
    ring: 'ring-cyan-500/20',
    header: 'from-cyan-500/12 via-cyan-500/5 to-transparent',
    border: 'border-cyan-500/20',
    iconBg: 'bg-cyan-500/15 text-cyan-400',
    dot: 'bg-cyan-400',
  },
  emerald: {
    icon: Lightbulb,
    accent: 'text-emerald-400',
    ring: 'ring-emerald-500/20',
    header: 'from-emerald-500/12 via-emerald-500/5 to-transparent',
    border: 'border-emerald-500/20',
    iconBg: 'bg-emerald-500/15 text-emerald-400',
    dot: 'bg-emerald-400',
  },
  amber: {
    icon: ShieldAlert,
    accent: 'text-amber-400',
    ring: 'ring-amber-500/20',
    header: 'from-amber-500/12 via-amber-500/5 to-transparent',
    border: 'border-amber-500/20',
    iconBg: 'bg-amber-500/15 text-amber-400',
    dot: 'bg-amber-400',
  },
}

function inferMarketSectionLayout(section) {
  const title = section.title || ''
  if (title.includes('梦境') || title.includes('指标')) return 'stats'
  if (title.includes('模板')) return 'templates'
  if (title.includes('六维') || title.includes('拉片')) return 'timeline'
  if (title.includes('热点') || title.includes('市场')) return 'insight'
  return 'stack'
}

function MarketKpiTile({ label, value, index }) {
  const isLong = String(value || '').length > 6
  const accents = [
    'from-gold-500/15 to-gold-500/5 border-gold-500/25 text-gold-300',
    'from-cyan-500/15 to-cyan-500/5 border-cyan-500/25 text-cyan-300',
    'from-emerald-500/15 to-emerald-500/5 border-emerald-500/25 text-emerald-300',
    'from-violet-500/15 to-violet-500/5 border-violet-500/25 text-violet-300',
  ]
  const accent = accents[index % accents.length]

  return (
    <div className={`rounded-xl border bg-gradient-to-br px-4 py-3.5 ${accent}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wider opacity-80">{label}</p>
      <p
        className={`mt-1.5 font-bold text-white break-words ${
          isLong ? 'text-sm leading-snug' : 'text-2xl tabular-nums'
        }`}
      >
        {value}
      </p>
    </div>
  )
}

function MarketStatPill({ item }) {
  const meta = parseScoreMeta(item.body)
  if (!meta) {
    return <MarketReportItem item={item} />
  }

  return (
    <div className="flex flex-col items-center rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.06] to-transparent px-4 py-5 text-center">
      <div className="relative mb-3 h-16 w-16">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36" aria-hidden>
          <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="2.5" />
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="#fbbf24"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray={`${meta.percent} 100`}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-lg font-bold tabular-nums text-white">
          {meta.num}
        </span>
      </div>
      <p className="text-xs font-semibold text-slate-300">{item.title}</p>
      <p className="mt-0.5 text-[10px] text-slate-500">满分 {meta.max}</p>
    </div>
  )
}

function MarketTemplateCard({ item, index }) {
  return (
    <article className="group relative overflow-hidden rounded-xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/8 via-white/[0.03] to-transparent p-4 transition-all hover:border-emerald-500/35 hover:shadow-lg hover:shadow-emerald-500/5">
      <div className="mb-3 flex items-center gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 text-sm font-bold text-emerald-300 ring-1 ring-emerald-500/30">
          {index + 1}
        </span>
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400/90">{item.title}</p>
      </div>
      <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words pl-11">{item.body}</p>
    </article>
  )
}

function MarketTimelineItem({ item, index, isLast, tone }) {
  return (
    <li className="relative flex gap-4 pb-5 last:pb-0">
      <div className="flex flex-col items-center shrink-0 pt-1">
        <span className={`flex h-3 w-3 rounded-full ring-4 ${tone.ring} ${tone.dot}`} />
        {!isLast ? <span className="mt-1 w-px flex-1 min-h-[24px] bg-white/10" aria-hidden /> : null}
      </div>
      <article className="min-w-0 flex-1 -mt-0.5 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3.5">
        <h6 className="text-xs font-semibold text-cyan-300 mb-2">{item.title}</h6>
        <p className="text-sm text-slate-300 leading-7 whitespace-pre-wrap break-words">{item.body}</p>
      </article>
    </li>
  )
}

function MarketInsightItem({ item, featured }) {
  if (featured) {
    return (
      <article className="col-span-full rounded-2xl border border-gold-500/25 bg-gradient-to-br from-gold-500/10 via-white/[0.04] to-transparent p-5">
        <div className="mb-2 flex items-center gap-2">
          <Users className="h-4 w-4 text-gold-400" />
          <h6 className="text-xs font-semibold uppercase tracking-wide text-gold-300">{item.title}</h6>
        </div>
        <p className="text-[15px] leading-8 text-slate-100 whitespace-pre-wrap break-words">{item.body}</p>
      </article>
    )
  }

  return (
    <article className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:border-gold-500/20 transition-colors">
      <h6 className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-400">
        <Flame className="h-3.5 w-3.5 text-gold-400/80" />
        {item.title}
      </h6>
      <p className="text-sm text-slate-300 leading-7 whitespace-pre-wrap break-words">{item.body}</p>
    </article>
  )
}

function MarketReportItem({ item }) {
  const variant = item.variant || 'default'
  const variantClass =
    variant === 'highlight'
      ? 'border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 to-transparent'
      : variant === 'warning'
        ? 'border-amber-500/25 bg-amber-500/8'
        : variant === 'accent'
          ? 'border-cyan-500/25 bg-cyan-500/8'
          : 'border-white/10 bg-white/[0.03]'

  return (
    <article className={`relative overflow-hidden rounded-xl border pl-4 pr-4 py-3.5 ${variantClass}`}>
      <span className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-gradient-to-b from-gold-400/80 to-cyan-400/40" />
      <h6 className="text-xs font-semibold text-slate-400 mb-2 pl-2">{item.title}</h6>
      <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap break-words pl-2">{item.body}</p>
    </article>
  )
}

function MarketReportSection({ section }) {
  const tone = MARKET_SECTION_STYLES[section.tone] || MARKET_SECTION_STYLES.indigo
  const Icon = tone.icon
  const items = section.items || []
  const layout = inferMarketSectionLayout(section)
  if (!items.length) return null

  return (
    <section className={`overflow-hidden rounded-2xl border shadow-lg shadow-black/10 ${tone.border}`}>
      <header className={`flex items-center gap-3 border-b px-5 py-4 bg-gradient-to-r ${tone.header} ${tone.border}`}>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone.iconBg}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <h5 className="text-sm font-semibold text-slate-50">{section.title}</h5>
          <p className="text-[11px] text-slate-500 mt-0.5">{items.length} 项洞察</p>
        </div>
      </header>

      {layout === 'stats' ? (
        <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
          {items.map((item, index) => (
            <MarketStatPill key={`${section.title}-${item.title}-${index}`} item={item} />
          ))}
        </div>
      ) : null}

      {layout === 'templates' ? (
        <div className="space-y-3 p-4">
          {items.map((item, index) => (
            <MarketTemplateCard key={`${section.title}-${index}`} item={item} index={index} />
          ))}
        </div>
      ) : null}

      {layout === 'timeline' ? (
        <ol className="p-5 pt-4">
          {items.map((item, index) => (
            <MarketTimelineItem
              key={`${section.title}-${item.title}-${index}`}
              item={item}
              index={index}
              isLast={index === items.length - 1}
              tone={tone}
            />
          ))}
        </ol>
      ) : null}

      {layout === 'insight' ? (
        <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
          {items.map((item, index) => (
            <MarketInsightItem
              key={`${section.title}-${item.title}-${index}`}
              item={item}
              featured={index === 0}
            />
          ))}
        </div>
      ) : null}

      {layout === 'stack' ? (
        <div className="space-y-3 p-4">
          {items.map((item, index) => (
            <MarketReportItem key={`${section.title}-${item.title}-${index}`} item={item} />
          ))}
        </div>
      ) : null}
    </section>
  )
}

function MarketReportBlock({ block }) {
  const metrics = block.metrics || []
  const sections = block.sections || []
  if (!block.drama_name && !metrics.length && !sections.length) return null

  return (
    <article className="space-y-5">
      {block.drama_name ? (
        <header className="relative overflow-hidden rounded-2xl border border-gold-500/20 bg-gradient-to-br from-gold-600/20 via-navy-900/70 to-cyan-500/10 px-6 py-6 shadow-xl shadow-black/15">
          <div className="pointer-events-none absolute -right-10 top-0 h-32 w-32 rounded-full bg-gold-500/10 blur-2xl" />
          <div className="relative flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15 backdrop-blur-sm">
              <BarChart3 className="h-5 w-5 text-gold-300" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-300/90">市场分析报告</p>
              <h3 className="mt-1.5 text-xl font-bold leading-snug text-white break-words sm:text-2xl">
                {block.drama_name}
              </h3>
            </div>
          </div>
        </header>
      ) : null}

      {metrics.length ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {metrics.map((item, index) => (
            <MarketKpiTile key={`metric-${item.label}-${index}`} label={item.label} value={item.value} index={index} />
          ))}
        </div>
      ) : null}

      {sections.map((section, index) => (
        <MarketReportSection key={`market-sec-${section.title}-${index}`} section={section} />
      ))}
    </article>
  )
}

const BRIEF_ITEM_VARIANTS = {
  default: 'border-white/10 bg-white/[0.03]',
  accent: 'border-cyan-500/25 bg-gradient-to-br from-cyan-500/8 to-transparent',
  highlight: 'border-gold-500/25 bg-gradient-to-br from-gold-500/10 to-transparent',
}

const BRIEF_SECTION_STYLES = {
  gold: {
    icon: Target,
    border: 'border-gold-500/20',
    header: 'from-gold-500/12 via-gold-500/5 to-transparent',
    iconBg: 'bg-gold-500/15 text-gold-400',
  },
  indigo: {
    icon: Users,
    border: 'border-cyan-500/20',
    header: 'from-cyan-500/12 via-cyan-500/5 to-transparent',
    iconBg: 'bg-cyan-500/15 text-cyan-400',
  },
}

function BriefStackItem({ item }) {
  const styleClass = BRIEF_ITEM_VARIANTS[item.variant] || BRIEF_ITEM_VARIANTS.default
  return (
    <article className={`relative overflow-hidden rounded-xl border px-4 py-4 ${styleClass}`}>
      <span className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-gradient-to-b from-gold-400/80 to-cyan-400/30" />
      <h6 className="pl-2 text-xs font-semibold uppercase tracking-wide text-gold-300/90">{item.title}</h6>
      <p className="mt-2 pl-2 text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{item.body}</p>
    </article>
  )
}

function BriefHookRatingCard({ item }) {
  const gradeStyle = gradeBadgeStyle(item.grade)
  return (
    <article className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-lg shadow-black/10">
      <div className="flex items-start gap-3">
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-lg font-black shadow-md ${gradeStyle}`}
        >
          {item.grade}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-slate-400">{item.title}</p>
          <p className="mt-2 text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{item.body}</p>
        </div>
      </div>
    </article>
  )
}

function ProjectBriefSection({ section }) {
  const tone = BRIEF_SECTION_STYLES[section.tone] || BRIEF_SECTION_STYLES.gold
  const Icon = tone.icon
  const items = section.items || []
  const layout = section.layout || 'stack'
  if (!items.length) return null

  return (
    <section className={`overflow-hidden rounded-2xl border shadow-lg shadow-black/10 ${tone.border}`}>
      <header className={`flex items-center gap-3 border-b px-5 py-4 bg-gradient-to-r ${tone.header} ${tone.border}`}>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone.iconBg}`}>
          <Icon className="h-4 w-4" />
        </div>
        <h5 className="text-sm font-semibold text-slate-50">{section.title}</h5>
      </header>

      {layout === 'insight' ? (
        <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
          {items.map((item, index) => (
            <MarketInsightItem
              key={`${section.title}-${item.title}-${index}`}
              item={item}
              featured={index === 0 || item.variant === 'highlight'}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-3 p-4">
          {items.map((item, index) => (
            <BriefStackItem key={`${section.title}-${item.title}-${index}`} item={item} />
          ))}
        </div>
      )}
    </section>
  )
}

function BriefSellingPointItem({ item }) {
  return (
    <li className="flex w-full min-w-0 gap-3 items-start">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-gold-500 to-amber-600 text-sm font-bold text-navy-950 shadow-lg shadow-gold-500/20">
        {item.index}
      </span>
      <div className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5">
        {item.title ? (
          <>
            <p className="text-sm font-semibold text-gold-200 break-words">{item.title}</p>
            {item.body ? (
              <p className="mt-2 text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{item.body}</p>
            ) : null}
          </>
        ) : (
          <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{item.body}</p>
        )}
      </div>
    </li>
  )
}

function ProjectBriefBlock({ block }) {
  const metrics = block.metrics || []
  const sections = block.sections || []
  const hookRatings = block.hook_ratings || []
  const sellingPoints = block.selling_points || []
  if (
    !block.headline
    && !block.opening_hook
    && !metrics.length
    && !sections.length
    && !hookRatings.length
    && !sellingPoints.length
  ) {
    return null
  }

  return (
    <article className="space-y-6">
      {block.headline ? (
        <header className="relative overflow-hidden rounded-2xl border border-gold-500/25 bg-gradient-to-br from-gold-600/15 via-navy-900/85 to-violet-950/25 px-6 py-6 shadow-xl shadow-black/15">
          <div className="pointer-events-none absolute -right-12 top-0 h-40 w-40 rounded-full bg-gold-500/10 blur-3xl" />
          <div className="relative flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-gold-500/20">
              <BookOpen className="h-5 w-5 text-gold-300" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-300/90">立项简报 · 核心目标</p>
              <h3 className="mt-2 text-lg font-bold leading-8 text-white break-words sm:text-xl">
                {block.headline}
              </h3>
            </div>
          </div>
        </header>
      ) : null}

      {block.opening_hook ? (
        <div className="relative overflow-hidden rounded-2xl border border-cyan-500/25 bg-gradient-to-r from-cyan-500/10 via-navy-900/50 to-transparent px-5 py-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
              <Clapperboard className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-cyan-300">跨段入场 · 开场钩子</p>
              <p className="mt-2 text-[15px] leading-8 text-slate-100 whitespace-pre-wrap break-words">
                {block.opening_hook}
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {metrics.length ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {metrics.map((item, index) => (
            <MarketStatPill
              key={`brief-metric-${item.label}-${index}`}
              item={{ title: item.label, body: item.value }}
            />
          ))}
        </div>
      ) : null}

      {hookRatings.length ? (
        <section className="space-y-4">
          <SectionTitle>S / A / B 钩子评级</SectionTitle>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {hookRatings.map((item, index) => (
              <BriefHookRatingCard key={`hook-${item.grade}-${index}`} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      {sections.map((section, index) => (
        <ProjectBriefSection key={`brief-sec-${section.title}-${index}`} section={section} />
      ))}

      {sellingPoints.length ? (
        <section>
          <SectionTitle>差异化卖点</SectionTitle>
          <ol className="mt-4 list-none space-y-3 p-0 m-0">
            {sellingPoints.map((item) => (
              <BriefSellingPointItem key={`sell-${item.index}-${item.title || item.body?.slice(0, 24)}`} item={item} />
            ))}
          </ol>
        </section>
      ) : null}
    </article>
  )
}

function WorldSceneCard({ scene, index }) {
  return (
    <article className="relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/8 via-white/[0.03] to-transparent p-5">
      <div className="mb-3 flex items-center gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-500/15 text-sm font-bold text-cyan-300 ring-1 ring-cyan-500/25">
          {scene.marker || index + 1}
        </span>
        <h6 className="text-sm font-semibold text-cyan-200 break-words">{scene.title}</h6>
      </div>
      <p className="text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words pl-12">{scene.body}</p>
    </article>
  )
}

function WorldRuleItem({ item }) {
  return (
    <li className="flex gap-3 items-start">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-purple-600 text-sm font-bold text-white shadow-lg shadow-violet-500/20">
        {item.index}
      </span>
      <div className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5">
        {item.title ? (
          <>
            <p className="text-sm font-semibold text-violet-200 break-words">{item.title}</p>
            {item.body ? (
              <p className="mt-2 text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{item.body}</p>
            ) : null}
          </>
        ) : (
          <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{item.body}</p>
        )}
      </div>
    </li>
  )
}

function WorldSettingBlock({ block }) {
  const spaceScenes = block.space_scenes || []
  const coreRules = block.core_rules || []
  if (
    !block.era_background
    && !block.space_intro
    && !spaceScenes.length
    && !block.power_structure
    && !coreRules.length
    && !block.forbidden_constraint
  ) {
    return null
  }

  return (
    <article className="space-y-6">
      {block.era_background ? (
        <header className="relative overflow-hidden rounded-2xl border border-violet-500/25 bg-gradient-to-br from-violet-600/15 via-navy-900/85 to-cyan-950/25 px-6 py-6 shadow-xl shadow-black/15">
          <div className="pointer-events-none absolute -right-12 top-0 h-40 w-40 rounded-full bg-violet-500/10 blur-3xl" />
          <div className="relative flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-violet-500/20">
              <Globe2 className="h-5 w-5 text-violet-300" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300/90">世界观 · 时代背景</p>
              <p className="mt-2 text-lg font-medium leading-8 text-white whitespace-pre-wrap break-words sm:text-xl">
                {block.era_background}
              </p>
            </div>
          </div>
        </header>
      ) : null}

      {block.space_intro || spaceScenes.length ? (
        <section className="space-y-4">
          <SectionTitle>核心空间</SectionTitle>
          {block.space_intro ? (
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/8 px-4 py-3">
              <p className="text-sm font-medium text-cyan-200">{block.space_intro}</p>
            </div>
          ) : null}
          {spaceScenes.length ? (
            <div className={`grid gap-4 ${spaceScenes.length > 1 ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
              {spaceScenes.map((scene, index) => (
                <WorldSceneCard key={`scene-${scene.title}-${index}`} scene={scene} index={index} />
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {block.power_structure ? (
        <section className="overflow-hidden rounded-2xl border border-gold-500/20 shadow-lg shadow-black/10">
          <header className="flex items-center gap-3 border-b border-gold-500/20 bg-gradient-to-r from-gold-500/12 to-transparent px-5 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-500/15 text-gold-400">
              <Users className="h-4 w-4" />
            </div>
            <h5 className="text-sm font-semibold text-slate-50">权力结构</h5>
          </header>
          <div className="p-5">
            <p className="text-sm leading-8 text-slate-200 whitespace-pre-wrap break-words">{block.power_structure}</p>
          </div>
        </section>
      ) : null}

      {coreRules.length ? (
        <section>
          <SectionTitle>核心规则</SectionTitle>
          <ol className="mt-4 list-none space-y-3 p-0 m-0">
            {coreRules.map((item) => (
              <WorldRuleItem key={`rule-${item.index}-${item.title || item.body?.slice(0, 24)}`} item={item} />
            ))}
          </ol>
        </section>
      ) : null}

      {block.forbidden_constraint ? (
        <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-red-950/20 to-transparent px-5 py-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-amber-400">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">禁忌约束</p>
              <p className="mt-2 text-sm leading-7 text-amber-100/95 whitespace-pre-wrap break-words">
                {block.forbidden_constraint}
              </p>
            </div>
          </div>
        </div>
      ) : null}
    </article>
  )
}

const MCKEE_FIELD_STYLES = {
  want: 'border-gold-500/20 bg-gold-500/8',
  need: 'border-cyan-500/20 bg-cyan-500/8',
  ghost: 'border-violet-500/20 bg-violet-500/8',
  lie: 'border-amber-500/20 bg-amber-500/8',
  flaw: 'border-rose-500/20 bg-rose-500/8',
}

const MCKEE_FIELDS = [
  { key: 'want', label: '表层欲望' },
  { key: 'need', label: '深层需求' },
  { key: 'ghost', label: '心魔' },
  { key: 'lie', label: '错误信念' },
  { key: 'flaw', label: '缺陷' },
]

function DreamCheckBanner({ dreamCheck }) {
  if (!dreamCheck || (!dreamCheck.note && dreamCheck.safety_score == null)) return null
  const blocking = dreamCheck.is_blocking === true
  const passed = dreamCheck.is_blocking === false

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border px-5 py-4 ${
        blocking
          ? 'border-red-500/30 bg-gradient-to-r from-red-500/10 to-transparent'
          : 'border-emerald-500/25 bg-gradient-to-r from-emerald-500/10 to-transparent'
      }`}
    >
      <div className="flex flex-wrap items-start gap-4">
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
            blocking ? 'bg-red-500/15 text-red-400' : 'bg-emerald-500/15 text-emerald-400'
          }`}
        >
          {blocking ? <XCircle className="h-5 w-5" /> : <CheckCircle2 className="h-5 w-5" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-100">梦境校验</p>
            {dreamCheck.safety_score != null ? (
              <span className="rounded-md border border-white/10 bg-white/10 px-2 py-0.5 text-xs font-bold tabular-nums text-white">
                安全感 {dreamCheck.safety_score}/10
              </span>
            ) : null}
            {passed ? (
              <span className="text-xs text-emerald-300">未触发熔断 · 可进入后续流程</span>
            ) : null}
            {blocking ? <span className="text-xs text-red-300">已触发熔断</span> : null}
          </div>
          {dreamCheck.note ? (
            <p className="mt-2 text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{dreamCheck.note}</p>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function MckeeCharacterCard({ character, variant }) {
  const isProtagonist = variant === 'protagonist'
  const headerBorder = isProtagonist ? 'border-gold-500/25 from-gold-500/12' : 'border-cyan-500/20 from-cyan-500/10'
  const avatarClass = isProtagonist
    ? 'border-gold-500/30 bg-gold-500/15 text-gold-300'
    : 'border-cyan-500/30 bg-cyan-500/15 text-cyan-300'

  const mckeeRows = MCKEE_FIELDS.filter((field) => character[field.key])

  return (
    <article className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] shadow-xl shadow-black/10">
      <header className={`border-b bg-gradient-to-r to-transparent px-5 py-4 ${headerBorder}`}>
        <div className="flex items-start gap-3">
          <div
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border text-lg font-bold ${avatarClass}`}
          >
            {characterInitial(character.name)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h6 className="text-lg font-bold text-slate-50 break-words">{character.name}</h6>
              {character.char_id ? (
                <span className="rounded-md border border-white/10 bg-white/10 px-2 py-0.5 text-[11px] font-medium text-slate-300">
                  {character.char_id}
                </span>
              ) : null}
              {character.age ? (
                <span className="text-xs text-slate-500">{character.age} 岁</span>
              ) : null}
            </div>
            {character.role_label ? (
              <span
                className={`mt-2 inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium ${roleBadgeClass(character.role_label)}`}
              >
                {character.role_label}
              </span>
            ) : null}
          </div>
        </div>
      </header>

      <div className="space-y-4 p-5">
        {mckeeRows.length ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {mckeeRows.map((field) => (
              <div
                key={`${character.char_id}-${field.key}`}
                className={`rounded-xl border px-3.5 py-3 ${MCKEE_FIELD_STYLES[field.key]}`}
              >
                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{field.label}</p>
                <p className="mt-1.5 text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">
                  {character[field.key]}
                </p>
              </div>
            ))}
          </div>
        ) : null}

        {character.arc ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-gold-400/90">人物弧光</p>
            <p className="mt-2 text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{character.arc}</p>
          </div>
        ) : null}

        {(character.timbre_tag || character.visual_tag) ? (
          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            {character.timbre_tag ? (
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-violet-500/20 bg-violet-500/8 px-3 py-1.5 text-xs text-violet-200">
                <Heart className="h-3.5 w-3.5 shrink-0" />
                {character.timbre_tag}
              </span>
            ) : null}
            {character.visual_tag ? (
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/20 bg-cyan-500/8 px-3 py-1.5 text-xs text-cyan-200">
                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                {character.visual_tag}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  )
}

function RelationRoleCard({ character }) {
  return (
    <article className="rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/8 to-transparent p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-violet-500/30 bg-violet-500/15 text-sm font-bold text-violet-300">
          {characterInitial(character.name)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h6 className="text-sm font-semibold text-slate-100">{character.name}</h6>
            {character.char_id ? (
              <span className="text-[10px] text-slate-500">{character.char_id}</span>
            ) : null}
            {character.age ? <span className="text-[10px] text-slate-500">{character.age}岁</span> : null}
          </div>
          {character.relation ? (
            <p className="mt-2 text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{character.relation}</p>
          ) : null}
          {character.visual_tag ? (
            <p className="mt-2 text-xs leading-relaxed text-violet-200/90">{character.visual_tag}</p>
          ) : null}
        </div>
      </div>
    </article>
  )
}

function CharacterBibleBlock({ block }) {
  const protagonists = block.protagonists || []
  const supporting = block.supporting_roles || []
  const relationRoles = block.relation_roles || []
  const relationships = block.relationships || []
  const dreamCheck = block.dream_check || {}

  if (
    !protagonists.length
    && !supporting.length
    && !relationRoles.length
    && !relationships.length
    && !dreamCheck.note
  ) {
    return null
  }

  return (
    <article className="space-y-6">
      <DreamCheckBanner dreamCheck={dreamCheck} />

      {protagonists.length ? (
        <section className="space-y-4">
          <SectionTitle>主角档案</SectionTitle>
          <div className={`grid gap-5 ${protagonists.length > 1 ? 'xl:grid-cols-2' : 'grid-cols-1'}`}>
            {protagonists.map((character, index) => (
              <MckeeCharacterCard
                key={`proto-${character.char_id || character.name}-${index}`}
                character={character}
                variant="protagonist"
              />
            ))}
          </div>
        </section>
      ) : null}

      {supporting.length ? (
        <section className="space-y-4">
          <SectionTitle>核心配角</SectionTitle>
          <div className="grid gap-5 lg:grid-cols-2">
            {supporting.map((character, index) => (
              <MckeeCharacterCard
                key={`support-${character.char_id || character.name}-${index}`}
                character={character}
                variant="supporting"
              />
            ))}
          </div>
        </section>
      ) : null}

      {relationRoles.length ? (
        <section className="space-y-4">
          <SectionTitle>关系角色</SectionTitle>
          <div className="grid gap-3 sm:grid-cols-2">
            {relationRoles.map((character, index) => (
              <RelationRoleCard key={`rel-role-${character.char_id || character.name}-${index}`} character={character} />
            ))}
          </div>
        </section>
      ) : null}

      {relationships.length ? (
        <RelationshipGraphBlock block={{ items: relationships }} />
      ) : null}
    </article>
  )
}

const STAGE_TONE = {
  opening: 'from-gold-500/20 border-gold-500/30 text-gold-300',
  warming: 'from-cyan-500/15 border-cyan-500/30 text-cyan-300',
  climax: 'from-rose-500/15 border-rose-500/30 text-rose-300',
  turning: 'from-violet-500/15 border-violet-500/30 text-violet-300',
  sprint: 'from-amber-500/15 border-amber-500/30 text-amber-300',
  ending: 'from-emerald-500/15 border-emerald-500/30 text-emerald-300',
}

function SixStageTimeline({ stages }) {
  if (!stages.length) return null
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-500">六段结构</p>
      <div className="flex h-3 overflow-hidden rounded-full bg-white/10">
        {stages.map((stage) => {
          const width = Math.max(Number(stage.proportion) || 0, 4)
          const tone = STAGE_TONE[stage.key] || 'from-slate-500/20 border-slate-500/30'
          return (
            <div
              key={`stage-bar-${stage.key || stage.index}`}
              className={`h-full bg-gradient-to-r ${tone.split(' ')[0]}`}
              style={{ width: `${width}%` }}
              title={`${stage.title} ${stage.subtitle || ''}`}
            />
          )
        })}
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {stages.map((stage) => {
          const tone = STAGE_TONE[stage.key] || 'from-slate-500/10 border-white/10 text-slate-300'
          return (
            <article
              key={`stage-meta-${stage.key || stage.index}`}
              className={`rounded-xl border bg-gradient-to-br to-transparent px-3.5 py-3 ${tone}`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-100">{stage.title}</p>
                {stage.proportion != null ? (
                  <span className="text-xs font-bold tabular-nums opacity-80">{stage.proportion}%</span>
                ) : null}
              </div>
              {stage.subtitle ? <p className="mt-1 text-[11px] text-slate-400">{stage.subtitle}</p> : null}
              {stage.summary ? (
                <p className="mt-2 text-xs leading-6 text-slate-300 line-clamp-3">{stage.summary}</p>
              ) : null}
            </article>
          )
        })}
      </div>
    </section>
  )
}

function ForeshadowingCard({ item }) {
  return (
    <article className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        {item.type ? (
          <span className="rounded-md border border-violet-500/25 bg-violet-500/10 px-2 py-0.5 text-[11px] font-semibold text-violet-300">
            {item.type}
          </span>
        ) : null}
        {item.buried != null && item.payoff != null ? (
          <span className="text-[11px] font-medium text-gold-400 tabular-nums">
            第{item.buried}集 → 第{item.payoff}集
          </span>
        ) : null}
      </div>
      <p className="text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{item.content}</p>
    </article>
  )
}

function parseRangeStart(rangeLabel) {
  if (!rangeLabel || typeof rangeLabel !== 'string') return 1
  const match = rangeLabel.match(/^(\d+)/)
  return match ? Number(match[1]) : 1
}

function SeriesOutlineBlock({ block }) {
  const stages = block.stages || []
  const foreshadowing = block.foreshadowing || []
  const allEpisodes = block.episodes || []
  const batches = block.episode_batches || []
  const planned = block.total_episodes || 0
  const generated = block.generated_episodes ?? allEpisodes.length
  const missingCount = (block.missing_episodes || []).length

  const defaultBatchStart = parseRangeStart(block.suggested_range)
  const initialBatchIndex = Math.max(
    0,
    batches.findIndex((b) => defaultBatchStart >= b.start && defaultBatchStart <= b.end),
  )
  const [activeBatchIndex, setActiveBatchIndex] = useState(initialBatchIndex >= 0 ? initialBatchIndex : 0)
  const [showStages, setShowStages] = useState(false)

  useEffect(() => {
    const idx = batches.findIndex((b) => defaultBatchStart >= b.start && defaultBatchStart <= b.end)
    if (idx >= 0) setActiveBatchIndex(idx)
  }, [block.suggested_range, batches.length, defaultBatchStart])

  const activeBatch = batches[activeBatchIndex] || null
  const progressPct = planned > 0 ? Math.min(100, Math.round((generated / planned) * 100)) : 0

  if (!stages.length && !foreshadowing.length && !allEpisodes.length && !planned && !batches.length) {
    return null
  }

  return (
    <article className="space-y-6">
      {planned ? (
        <div className="rounded-2xl border border-gold-500/20 bg-gradient-to-r from-gold-500/10 to-transparent px-5 py-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-4 flex-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold-500/15 text-gold-400">
                <BookOpen className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-300/90">系列大纲</p>
                <p className="text-2xl font-bold tabular-nums text-white">
                  已生成 {generated}
                  <span className="mx-1 text-sm font-medium text-slate-500">/</span>
                  {planned}
                  <span className="ml-1 text-sm font-medium text-slate-400">集</span>
                </p>
              </div>
            </div>
            {missingCount > 0 ? (
              <div className="text-xs text-cyan-300/90 bg-cyan-500/10 border border-cyan-500/20 rounded-xl px-3 py-2">
                尚有 {missingCount} 集待生成
                {block.suggested_range ? ` · 建议下一批 ${block.suggested_range}` : ''}
              </div>
            ) : (
              <div className="text-xs text-emerald-300/90 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2">
                分集大纲已全部生成
              </div>
            )}
          </div>
          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-gold-500 to-amber-400 transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      ) : null}

      {batches.length ? (
        <section className="space-y-3">
          <SectionTitle>分集大纲（按批次浏览）</SectionTitle>
          <div className="flex flex-wrap gap-1.5">
            {batches.map((batch, index) => {
              const isActive = index === activeBatchIndex
              const complete = batch.generated >= batch.total
              return (
                <button
                  key={`outline-batch-${batch.label}`}
                  type="button"
                  onClick={() => setActiveBatchIndex(index)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium border transition-all ${
                    isActive
                      ? 'bg-gold-500 text-navy-950 border-gold-500 shadow-gold'
                      : complete
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:border-emerald-400/50'
                        : 'bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30'
                  }`}
                >
                  {batch.label} 集
                  <span className="ml-1 opacity-80">({batch.generated}/{batch.total})</span>
                </button>
              )
            })}
          </div>
          {activeBatch ? (
            <div className="space-y-3">
              <p className="text-xs text-slate-500">
                当前查看：第 {activeBatch.start}-{activeBatch.end} 集
                {activeBatch.generated < activeBatch.total
                  ? ` · 本批已生成 ${activeBatch.generated} 集，其余待补`
                  : ' · 本批已全部生成'}
              </p>
              {activeBatch.episodes.map((ep) => (
                <EpisodeOutlineCard key={`batch-${activeBatch.label}-ep-${ep.episode_no}`} item={ep} />
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {stages.length ? (
        <section className="space-y-3">
          <button
            type="button"
            onClick={() => setShowStages((v) => !v)}
            className="flex items-center gap-2 text-sm font-semibold text-slate-300 hover:text-white"
          >
            {showStages ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            六阶段结构概览
          </button>
          {showStages ? <SixStageTimeline stages={stages} /> : null}
        </section>
      ) : null}

      {foreshadowing.length ? (
        <section className="space-y-3">
          <SectionTitle>伏笔清单</SectionTitle>
          <div className="grid gap-3 lg:grid-cols-2">
            {foreshadowing.map((item, index) => (
              <ForeshadowingCard key={`foreshadow-${item.type}-${index}`} item={item} />
            ))}
          </div>
        </section>
      ) : null}
    </article>
  )
}

function NarrativeBeatTimeline({ beats, beatTimeline }) {
  const items = (beats || []).length
    ? beats
    : (beatTimeline || []).map((beat) => {
        const match = String(beat).match(/^([^：:]+)[：:]([\s\S]+)$/)
        if (match) {
          return { time: match[1].trim(), content: match[2].trim() }
        }
        return { time: '', content: String(beat) }
      })
  if (!items.length) return null

  return (
    <ol className="relative space-y-0">
      {items.map((beat, index) => {
        const isLast = index === items.length - 1
        return (
          <li key={`beat-${index}`} className="relative flex gap-3 pb-4 last:pb-0">
            <div className="flex flex-col items-center shrink-0 w-5 pt-1">
              <span className="h-2.5 w-2.5 rounded-full bg-gold-500 ring-4 ring-gold-500/10" />
              {!isLast ? <span className="w-px flex-1 min-h-[12px] bg-gold-500/20 mt-1" aria-hidden /> : null}
            </div>
            <div className="min-w-0 flex-1 -mt-0.5">
              {beat.time ? (
                <span className="inline-flex rounded-md bg-gold-500/15 px-2 py-0.5 text-[11px] font-bold tabular-nums text-gold-300 border border-gold-500/20">
                  {beat.time}
                </span>
              ) : null}
              <p className={`text-sm leading-relaxed text-slate-200 break-words ${beat.time ? 'mt-1.5' : ''}`}>
                {beat.content}
              </p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function NarrativeMechanicCard({ item, index }) {
  return (
    <article className="relative overflow-hidden rounded-xl border border-cyan-500/20 bg-white/[0.04] px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur-sm">
      <span className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 to-cyan-600" aria-hidden />
      <div className="pl-2">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-cyan-400">机制 {index + 1}</p>
        <h6 className="mt-1 text-sm font-semibold text-slate-100 break-words">{item.title}</h6>
        <p className="mt-2 text-sm leading-7 text-slate-300 whitespace-pre-wrap break-words">{item.body}</p>
      </div>
    </article>
  )
}

function NarrativeEpisodeCard({ episode, isLast }) {
  const hasBeats = (episode.beats || episode.beat_timeline || []).length > 0
  const hasMeta = (episode.techniques || []).length > 0 || (episode.worldview_points || []).length > 0

  return (
    <article className="relative flex gap-4">
      <div className="flex flex-col items-center shrink-0 w-10 pt-1">
        <span className="flex h-10 w-10 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 text-white shadow-lg shadow-cyan-500/20">
          <span className="text-[9px] font-medium uppercase leading-none opacity-80">EP</span>
          <span className="text-sm font-bold tabular-nums leading-none mt-0.5">{episode.episode_no}</span>
        </span>
        {!isLast ? <span className="w-px flex-1 min-h-4 bg-cyan-500/20 my-2" aria-hidden /> : null}
      </div>

      <div className={`min-w-0 flex-1 ${isLast ? '' : 'pb-6'}`}>
        <div className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.04] shadow-lg shadow-black/5 backdrop-blur-sm">
          <div className="border-b border-white/10 bg-gradient-to-r from-white/[0.06] to-transparent px-4 py-3.5">
            <p className="text-sm font-semibold text-slate-100">{episode.title}</p>
            {episode.focus ? (
              <p className="mt-1.5 text-sm leading-relaxed text-slate-400 break-words">{episode.focus}</p>
            ) : null}
          </div>

          <div className="space-y-4 px-4 py-4">
            {episode.emotion_design ? (
              <div className="rounded-xl border border-rose-500/20 bg-gradient-to-br from-rose-500/10 to-transparent px-4 py-3">
                <p className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-rose-300">
                  <Heart className="h-3.5 w-3.5" />
                  观众情绪设计
                </p>
                <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">
                  {episode.emotion_design}
                </p>
              </div>
            ) : null}

            {hasBeats ? (
              <div>
                <p className="mb-3 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  <Clock className="h-3.5 w-3.5" />
                  竖屏节拍时间轴
                </p>
                <NarrativeBeatTimeline beats={episode.beats} beatTimeline={episode.beat_timeline} />
              </div>
            ) : null}

            {hasMeta ? (
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                {(episode.techniques || []).length ? (
                  <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/8 px-3.5 py-3">
                    <p className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-400">
                      <Lightbulb className="h-3.5 w-3.5" />
                      关键叙事技法
                    </p>
                    <ul className="space-y-1.5">
                      {episode.techniques.map((item, index) => (
                        <li key={`tech-${index}`} className="flex gap-2 text-sm leading-relaxed text-slate-200">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
                          <span className="break-words">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {(episode.worldview_points || []).length ? (
                  <div className="rounded-lg border border-sky-500/20 bg-sky-500/8 px-3.5 py-3">
                    <p className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-sky-300">
                      <Globe2 className="h-3.5 w-3.5" />
                      世界观传递点
                    </p>
                    <ul className="space-y-1.5">
                      {episode.worldview_points.map((item, index) => (
                        <li
                          key={`world-${index}`}
                          className="text-sm leading-relaxed text-slate-300 break-words"
                        >
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  )
}

function NarrativePlanBlock({ block }) {
  const episodes = block.episodes || []
  const mechanics = block.mechanics || []

  if (!block.core_objective && !block.target_range && !mechanics.length && !episodes.length) {
    return null
  }

  return (
    <article className="space-y-6">
      <header className="overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-600/20 via-navy-900/60 to-gold-500/10 px-6 py-6 text-white shadow-lg shadow-black/10 backdrop-blur-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
              <Clapperboard className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wider text-cyan-300/90">叙事工程方案</p>
              {block.target_range ? (
                <span className="mt-2 inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">
                  {block.target_range}
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {episodes.length ? (
              <span className="inline-flex items-center rounded-full border border-white/15 bg-white/8 px-3 py-1 text-xs font-medium">
                {episodes.length} 集设计
              </span>
            ) : null}
            {mechanics.length ? (
              <span className="inline-flex items-center rounded-full border border-white/15 bg-white/8 px-3 py-1 text-xs font-medium">
                {mechanics.length} 项机制
              </span>
            ) : null}
          </div>
        </div>
        {block.core_objective ? (
          <p className="mt-4 text-sm sm:text-[15px] leading-8 text-white/95 whitespace-pre-wrap break-words">
            {block.core_objective}
          </p>
        ) : null}
      </header>

      {mechanics.length ? (
        <section>
          <SectionTitle>叙事机制</SectionTitle>
          <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
            {mechanics.map((item, index) => (
              <NarrativeMechanicCard key={`mech-${item.title}-${index}`} item={item} index={index} />
            ))}
          </div>
        </section>
      ) : null}

      {episodes.length ? (
        <section>
          <SectionTitle>分集叙事设计</SectionTitle>
          <p className="mt-1 text-xs text-slate-500">按集数纵向浏览，每集含情绪曲线与竖屏节拍</p>
          <div className="mt-4 space-y-0">
            {episodes.map((episode, index) => (
              <NarrativeEpisodeCard
                key={`narr-ep-${episode.episode_no}`}
                episode={episode}
                isLast={index === episodes.length - 1}
              />
            ))}
          </div>
        </section>
      ) : null}

      {block.consistency_check ? (
        <section className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-5 py-4 shadow-lg shadow-black/5 backdrop-blur-sm">
          <div className="mb-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <p className="text-sm font-semibold text-emerald-300">叙事一致性校验</p>
          </div>
          <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap break-words">{block.consistency_check}</p>
        </section>
      ) : null}
    </article>
  )
}

function WorldSectionsBlock({ block }) {
  const sections = block.sections || []
  if (!sections.length) return null
  return (
    <section className="space-y-5">
      {sections.map((section, index) => {
        if (section.kind === 'paragraph') {
          return (
            <ParagraphBlock key={`ws-${index}`} block={{ title: section.title, text: section.text }} />
          )
        }
        if (section.kind === 'list') {
          return (
            <ListBlock key={`ws-${index}`} block={{ title: section.title, items: section.items || [] }} />
          )
        }
        return null
      })}
    </section>
  )
}

function AssessmentReportBlock({ block }) {
  const passed = block.passed
  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.04] overflow-hidden shadow-lg shadow-black/5 backdrop-blur-sm">
      <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between gap-3">
        <SectionTitle>{block.title}</SectionTitle>
        {passed === true ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-300 border border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />通过
          </span>
        ) : passed === false ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/15 px-2.5 py-1 text-xs font-medium text-rose-300 border border-rose-500/20">
            <XCircle className="h-3.5 w-3.5" />未通过
          </span>
        ) : null}
      </div>
      <div className="p-5 space-y-4">
        {(block.metrics || []).length > 0 ? (
          <MetricsBlock block={{ items: block.metrics }} />
        ) : null}
        {block.detail ? (
          <p className="text-sm text-slate-200 leading-7 whitespace-pre-wrap">{block.detail}</p>
        ) : null}
        {(block.notes || []).length > 0 ? (
          <ListBlock block={{ title: '说明', items: block.notes }} />
        ) : null}
      </div>
    </section>
  )
}

function EpisodeMetricsListBlock({ block }) {
  const episodes = block.episodes || []
  if (!episodes.length) return null
  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <div className={`space-y-3 ${block.title ? 'mt-3' : ''}`}>
        {episodes.map((ep, index) => (
          <article key={`${ep.episode_no || index}`} className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur-sm">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-slate-100">{ep.title}</p>
              {ep.subtitle ? (
                <span className="text-xs text-slate-400">{ep.subtitle}</span>
              ) : null}
            </div>
            {ep.body ? (
              <p className="mt-2 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap border-l-2 border-gold-500/30 pl-3">
                {ep.body}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  )
}

const BLOCK_RENDERERS = {
  metrics: MetricsBlock,
  hero: HeroBlock,
  kv: KvBlock,
  paragraph: ParagraphBlock,
  list: ListBlock,
  callout: CalloutBlock,
  steps: StepsBlock,
  outline_overview: OutlineOverviewBlock,
  stage_outlines: StageOutlinesBlock,
  cards: CardsBlock,
  review_overview: ReviewOverviewBlock,
  review_issues: ReviewIssuesBlock,
  verdict: VerdictBlock,
  compliance_report: ComplianceReportBlock,
  quality_report: QualityReportBlock,
  scoreboard: ScoreBoardBlock,
  score_board: ScoreBoardBlock,
  checks: ChecksBlock,
  script_episodes: ScriptEpisodesBlock,
  plan_overview: PlanOverviewBlock,
  plan_items: PlanItemsBlock,
  character_roster: CharacterRosterBlock,
  relationship_graph: RelationshipGraphBlock,
  market_report: MarketReportBlock,
  project_brief: ProjectBriefBlock,
  world_setting: WorldSettingBlock,
  character_bible: CharacterBibleBlock,
  series_outline: SeriesOutlineBlock,
  narrative_plan: NarrativePlanBlock,
  world_sections: WorldSectionsBlock,
  assessment_report: AssessmentReportBlock,
  episode_metrics_list: EpisodeMetricsListBlock,
}

function renderBlock(block, index) {
  if (!block || !block.type) return null
  const Renderer = BLOCK_RENDERERS[block.type]
  if (!Renderer) {
    if (block.text || block.title) {
      return (
        <div key={`fallback-${index}`} className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
          {block.title ? <p className="text-sm font-semibold text-slate-100 mb-2">{block.title}</p> : null}
          {block.text ? <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{block.text}</p> : null}
        </div>
      )
    }
    return null
  }
  return <Renderer key={`${block.type}-${index}`} block={block} />
}

function extractBlockList(view) {
  if (!view || typeof view !== 'object') return []
  const list = view.blocks || view.sections || view.items
  return Array.isArray(list) ? list : []
}

/** 兼容单 view 与 { artifact_key: view } 两种后端结构 */
export function normalizeOutputView(views, preferredArtifactKey) {
  if (!views || typeof views !== 'object') {
    return { view: null, blockList: [] }
  }

  const directBlocks = extractBlockList(views)
  if (directBlocks.length) {
    return { view: views, blockList: directBlocks }
  }

  const keys = Object.keys(views).filter((key) => views[key] && typeof views[key] === 'object')
  if (!keys.length) {
    return { view: views, blockList: [] }
  }

  const pickKey = preferredArtifactKey && views[preferredArtifactKey]
    ? preferredArtifactKey
    : keys[0]

  if (keys.length === 1 || (preferredArtifactKey && views[preferredArtifactKey])) {
    const view = views[pickKey]
    return { view, blockList: extractBlockList(view) }
  }

  const blockList = keys.flatMap((key) => extractBlockList(views[key]))
  return { view: views[pickKey], blockList }
}

function listRawArtifactKeys(rawArtifacts) {
  if (!rawArtifacts || typeof rawArtifacts !== 'object') return []
  return Object.keys(rawArtifacts).filter((key) => {
    const value = rawArtifacts[key]
    if (value == null || value === '') return false
    if (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0) return false
    return true
  })
}

function RawArtifactPanel({ rawArtifacts, artifactKey }) {
  const artifactKeys = useMemo(() => listRawArtifactKeys(rawArtifacts), [rawArtifacts])
  const defaultKey = artifactKey && rawArtifacts?.[artifactKey] != null ? artifactKey : artifactKeys[0]
  const [activeKey, setActiveKey] = useState(defaultKey)

  useEffect(() => {
    setActiveKey(defaultKey)
  }, [defaultKey])

  const formatted = formatPayloadText(rawArtifacts?.[activeKey])
  if (formatted.empty) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        暂无原始输出
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {artifactKeys.length > 1 ? (
        <div className="flex flex-wrap gap-1.5 rounded-xl border border-white/10 bg-black/20 p-1">
          {artifactKeys.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveKey(key)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                activeKey === key
                  ? 'bg-gold-500/20 text-gold-300 border border-gold-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {key}
            </button>
          ))}
        </div>
      ) : activeKey ? (
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{activeKey}</p>
      ) : null}
      <div className="rounded-xl border border-white/10 bg-black/30 overflow-hidden">
        <pre className="max-h-[min(70vh,720px)] overflow-auto whitespace-pre-wrap break-words p-4 text-[12px] leading-relaxed text-slate-200 font-mono">
          {formatted.text}
        </pre>
      </div>
      {formatted.truncated ? (
        <p className="text-xs text-amber-400/80">内容已截断，原始长度 {formatted.length}</p>
      ) : null}
    </div>
  )
}

function PresentationModeToggle({ mode, onChange, hasStructured }) {
  return (
    <div
      className="inline-flex rounded-xl border border-white/10 bg-black/25 p-1"
      role="tablist"
      aria-label="输出展示模式"
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'structured'}
        disabled={!hasStructured}
        onClick={() => onChange('structured')}
        className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
          mode === 'structured'
            ? 'bg-gold-500/20 text-gold-300 border border-gold-500/30'
            : hasStructured
              ? 'text-slate-400 hover:text-slate-200'
              : 'text-slate-600 cursor-not-allowed'
        }`}
      >
        结构化展示
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'raw'}
        onClick={() => onChange('raw')}
        className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
          mode === 'raw'
            ? 'bg-gold-500/20 text-gold-300 border border-gold-500/30'
            : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        原始 JSON
      </button>
    </div>
  )
}

export default function DramaPresentation({ views, rawArtifacts, artifactKey }) {
  const { blockList } = normalizeOutputView(views, artifactKey)
  const hasStructured = blockList.length > 0
  const hasRaw = listRawArtifactKeys(rawArtifacts).length > 0
  const [displayMode, setDisplayMode] = useState(hasStructured ? 'structured' : 'raw')

  useEffect(() => {
    setDisplayMode(hasStructured ? 'structured' : 'raw')
  }, [artifactKey, hasStructured])

  if (!hasStructured && !hasRaw) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        暂无结构化输出
      </div>
    )
  }

  const showStructured = displayMode === 'structured' && hasStructured
  const showToggle = hasStructured && hasRaw

  return (
    <div className="space-y-4">
      {showToggle ? (
        <div className="flex justify-end">
          <PresentationModeToggle
            mode={displayMode}
            onChange={setDisplayMode}
            hasStructured={hasStructured}
          />
        </div>
      ) : null}

      {showStructured ? (
        <div className="space-y-6">
          {blockList.map((block, index) => renderBlock(block, index))}
        </div>
      ) : (
        <RawArtifactPanel rawArtifacts={rawArtifacts} artifactKey={artifactKey} />
      )}
    </div>
  )
}

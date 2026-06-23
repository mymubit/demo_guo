import { useMemo, useState } from 'react'
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  Sparkles,
  XCircle,
  Zap,
} from 'lucide-react'

function SectionTitle({ children }) {
  return (
    <h5 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
      <span className="w-1 h-4 rounded-full bg-indigo-500" />
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
            className="rounded-xl bg-gradient-to-br from-indigo-50 to-white border border-indigo-100/80 px-4 py-3 shadow-sm"
          >
            <p className="text-[11px] font-medium text-indigo-600/90">{item.label}</p>
            <p className="text-xl font-bold text-gray-900 mt-1 tabular-nums">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function HeroBlock({ block }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-violet-50 px-5 py-4 shadow-sm">
      <Sparkles className="absolute right-4 top-4 h-5 w-5 text-indigo-200" />
      {block.title ? (
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 mb-2">{block.title}</p>
      ) : null}
      {block.subtitle ? (
        <p className="text-[15px] text-gray-800 leading-7 whitespace-pre-wrap pr-8">{block.subtitle}</p>
      ) : null}
    </div>
  )
}

function KvBlock({ block }) {
  const rows = block.rows || []
  if (!rows.length) return null

  const isTwoColumn = block.layout === 'columns_2'

  return (
    <section className="w-full rounded-xl border border-gray-200/80 overflow-hidden bg-white shadow-sm">
      {block.title ? (
        <div className="px-5 py-3.5 bg-gradient-to-r from-slate-50 to-white border-b border-gray-100">
          <SectionTitle>{block.title}</SectionTitle>
        </div>
      ) : null}
      <dl
        className={
          isTwoColumn
            ? 'grid gap-3 p-4 sm:grid-cols-2'
            : 'divide-y divide-gray-100'
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
                  ? `rounded-lg border border-gray-100 bg-gray-50/40 px-4 py-3.5 hover:bg-gray-50/80 transition-colors ${
                      spanFull ? 'sm:col-span-2' : ''
                    }`
                  : `px-5 py-4 ${isLong ? 'bg-white' : 'hover:bg-gray-50/60'} transition-colors`
              }
            >
              <dt className="text-xs font-semibold text-indigo-600 mb-2">{row.key}</dt>
              <dd
                className={`text-sm text-gray-800 leading-7 whitespace-pre-wrap ${
                  isLong && !isTwoColumn ? 'pl-3 border-l-2 border-indigo-100' : ''
                } ${isTwoColumn && isLong ? 'pl-3 border-l-2 border-indigo-100' : ''}`}
              >
                {row.value}
              </dd>
            </div>
          )
        })}
      </dl>
    </section>
  )
}

function ParagraphBlock({ block }) {
  return (
    <section className="rounded-xl border border-gray-100 bg-gray-50/50 px-4 py-4">
      {block.title ? <div className="mb-2"><SectionTitle>{block.title}</SectionTitle></div> : null}
      <p className="text-sm text-gray-800 leading-7 whitespace-pre-wrap">{block.text}</p>
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
            className="flex gap-2.5 text-sm text-gray-800 leading-relaxed"
          >
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function StepsBlock({ block }) {
  return (
    <section>
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      <ol className={`space-y-3 ${block.title ? 'mt-3' : ''}`}>
        {(block.items || []).map((item) => (
          <li key={`step-${item.index}-${item.title}`} className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white shadow-sm">
              {item.index}
            </span>
            <div className="min-w-0 flex-1 rounded-xl border border-gray-200/80 bg-white px-4 py-3 shadow-sm">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                {item.subtitle ? (
                  <span className="rounded-md bg-violet-50 px-2 py-0.5 text-[11px] font-medium text-violet-700">
                    {item.subtitle}
                  </span>
                ) : null}
              </div>
              {item.body ? (
                <p className="mt-2 text-sm text-gray-700 leading-7 whitespace-pre-wrap border-l-2 border-indigo-100 pl-3">
                  {item.body}
                </p>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}

const EMOTION_STYLES = {
  EV: 'bg-rose-50 text-rose-700 border-rose-100',
  ET: 'bg-sky-50 text-sky-800 border-sky-100',
  TP: 'bg-violet-50 text-violet-700 border-violet-100',
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
    <section className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div className="grid lg:grid-cols-[auto_1fr] divide-y lg:divide-y-0 lg:divide-x divide-gray-100">
        {block.total_episodes ? (
          <div className="flex items-center gap-4 px-5 py-4 lg:px-6 lg:py-5 lg:min-w-[140px]">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wide text-gray-400">总集数</p>
              <p className="text-3xl font-bold text-gray-900 tabular-nums leading-none mt-1">
                {block.total_episodes}
              </p>
            </div>
          </div>
        ) : null}

        <div className="divide-y divide-gray-100 min-w-0">
          {hasChecks ? (
            <div className="px-5 py-4 space-y-3">
              <p className="text-xs font-semibold text-gray-500">节奏校验</p>
              {(block.checks || []).map((check, index) => (
                <div key={`check-${index}`} className="flex gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                    <CheckCircle2 className="h-3 w-3" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-500">{check.label}</p>
                    <p className="mt-0.5 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                      {check.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {hasReverses ? (
            <div className="px-5 py-4">
              <p className="text-xs font-semibold text-gray-500 mb-2.5">A 级反转点</p>
              <div className="space-y-2">
                {(block.reverse_points || []).map((point, index) => (
                  <div
                    key={`reverse-${point.episode || index}`}
                    className="flex gap-3 rounded-lg bg-amber-50/60 border border-amber-100/80 px-3 py-2.5"
                  >
                    <span className="inline-flex shrink-0 items-center gap-1 rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-900">
                      <Zap className="h-3 w-3" />
                      {point.title}
                    </span>
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap min-w-0">
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
        const style = (key && EMOTION_STYLES[key]) || 'bg-gray-50 text-gray-700 border-gray-100'
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

function EpisodeStructureGrid({ structure }) {
  const items = (structure || []).filter(Boolean)
  if (!items.length) return null

  return (
    <div className="grid sm:grid-cols-2 gap-2">
      {items.map((part, index) => (
        <div key={`part-${index}`} className="rounded-lg bg-gray-50/80 px-3 py-2.5 border border-gray-100/80">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-400">{part.label}</p>
          <p className="mt-1 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{part.text}</p>
        </div>
      ))}
    </div>
  )
}

function EpisodeOutlineCard({ item, compact = false }) {
  const structure = item.structure?.length ? item.structure : (item.sections || []).filter(
    (s) => !emotionKey(s.label),
  )
  const emotions = item.emotions?.length
    ? item.emotions
    : (item.sections || []).filter((s) => emotionKey(s.label))

  return (
    <article
      className={`rounded-lg border border-gray-200 bg-white ${
        compact ? 'px-3.5 py-3' : 'px-4 py-3.5 shadow-sm'
      }`}
    >
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <h6 className="text-sm font-semibold text-gray-900">{item.title}</h6>
      </div>

      {item.subtitle ? (
        <blockquote className="mt-2.5 border-l-[3px] border-amber-400 bg-amber-50/50 px-3 py-2 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap not-italic">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-700/80 block mb-0.5">
            集末钩子
          </span>
          {item.subtitle}
        </blockquote>
      ) : null}

      {emotions.length > 0 ? (
        <div className={item.subtitle ? 'mt-3' : 'mt-2.5'}>
          <EpisodeEmotionRow emotions={emotions} />
        </div>
      ) : null}

      {structure.length > 0 ? (
        <div className="mt-3">
          <EpisodeStructureGrid structure={structure} />
        </div>
      ) : null}

      {(item.tags || []).filter(Boolean).length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {item.tags.filter(Boolean).map((tag, tagIndex) => (
            <span
              key={`${item.title}-tag-${tagIndex}`}
              className="rounded-md bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {item.body ? (
        <p className="mt-2 text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{item.body}</p>
      ) : null}
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
              className="text-gray-500 hover:text-indigo-600 transition-colors"
            >
              全部展开
            </button>
            <span className="text-gray-300">|</span>
            <button
              type="button"
              onClick={collapseAll}
              className="text-gray-500 hover:text-indigo-600 transition-colors"
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
              {/* 时间轴 */}
              <div className="flex flex-col items-center shrink-0 w-8 pt-1">
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold shadow-sm ${
                    isOpen
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-indigo-600 border-2 border-indigo-200'
                  }`}
                >
                  {stage.index}
                </span>
                {!isLast ? (
                  <span className="w-px flex-1 min-h-[16px] bg-gray-200 my-1" aria-hidden />
                ) : null}
              </div>

              {/* 阶段内容 */}
              <div className={`flex-1 min-w-0 ${isLast ? '' : 'pb-5'}`}>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <button
                    type="button"
                    onClick={() => toggleStage(stage.index)}
                    className="w-full flex items-start gap-3 px-4 py-3.5 text-left hover:bg-gray-50/80 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-gray-900">{stage.title}</p>
                        {stage.subtitle ? (
                          <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-[11px] font-medium text-gray-600">
                            {stage.subtitle}
                          </span>
                        ) : null}
                        <span className="text-xs text-gray-400">
                          {(stage.episodes || []).length} 集
                        </span>
                      </div>
                      {!isOpen && stage.summary ? (
                        <p className="mt-1.5 text-sm text-gray-500 leading-relaxed line-clamp-1">
                          {stage.summary}
                        </p>
                      ) : null}
                    </div>
                    {isOpen ? (
                      <ChevronUp className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
                    )}
                  </button>

                  {isOpen ? (
                    <div className="px-4 pb-4 border-t border-gray-100 space-y-4">
                      {(stage.summary || (stage.highlights || []).length > 0) ? (
                        <div className="pt-3 rounded-lg bg-slate-50/70 border border-gray-100 px-3.5 py-3 space-y-3.5">
                          {stage.summary ? (
                            <div>
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-600/90">
                                阶段目标
                              </p>
                              <p className="mt-1.5 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                {stage.summary}
                              </p>
                            </div>
                          ) : null}

                          {(stage.highlights || []).length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-600/90">
                                关键情节点
                              </p>
                              <ul className="mt-2 flex flex-wrap gap-2">
                                {stage.highlights.map((point, pointIndex) => (
                                  <li
                                    key={`stage-${stage.index}-point-${pointIndex}`}
                                    className="rounded-lg bg-white border border-indigo-100/70 px-3 py-1.5 text-xs text-gray-800 leading-relaxed max-w-full"
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
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
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

function CardsBlock({ block }) {
  const isStack = block.layout === 'stack'
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
  格式问题: 'bg-amber-50 text-amber-800 border-amber-100',
  逻辑冗余: 'bg-violet-50 text-violet-800 border-violet-100',
  结构问题: 'bg-sky-50 text-sky-800 border-sky-100',
  逻辑问题: 'bg-orange-50 text-orange-800 border-orange-100',
}

function reviewIssueStyle(issueType) {
  return REVIEW_ISSUE_STYLES[issueType] || 'bg-gray-50 text-gray-700 border-gray-100'
}

function ReviewOverviewBlock({ block }) {
  const passed = block.passed
  const pacingPassed = block.pacing_passed
  const issueCount = block.issue_count ?? 0

  return (
    <section className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div
        className={`px-4 py-4 border-b border-gray-100 ${
          passed === false ? 'bg-red-50/60' : 'bg-emerald-50/60'
        }`}
      >
        <div className="flex items-center gap-2">
          {passed === false ? (
            <XCircle className="h-5 w-5 text-red-600" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          )}
          <span
            className={`text-sm font-semibold ${
              passed === false ? 'text-red-800' : 'text-emerald-800'
            }`}
          >
            {passed === false ? '审查未通过' : passed === true ? '审查通过' : '审稿结论'}
          </span>
          {issueCount > 0 ? (
            <span className="rounded-full bg-white/80 border border-gray-200 px-2 py-0.5 text-[11px] text-gray-600">
              {issueCount} 项问题
            </span>
          ) : null}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-gray-100">
        {passed !== null && passed !== undefined ? (
          <div className="flex items-center gap-3 px-4 py-3.5">
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                passed ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'
              }`}
            >
              {passed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            </span>
            <div>
              <p className="text-xs text-gray-400">整体结论</p>
              <p className="text-sm font-medium text-gray-800">{passed ? '通过' : '未通过'}</p>
            </div>
          </div>
        ) : null}

        {pacingPassed !== null && pacingPassed !== undefined ? (
          <div className="flex items-center gap-3 px-4 py-3.5">
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                pacingPassed ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'
              }`}
            >
              {pacingPassed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            </span>
            <div>
              <p className="text-xs text-gray-400">节奏检查</p>
              <p className="text-sm font-medium text-gray-800">{pacingPassed ? '通过' : '未通过'}</p>
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
            className="rounded-xl border border-gray-200 bg-white px-4 py-3.5 shadow-sm"
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
                <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-700">
                  第{item.episode_number}集
                </span>
              ) : null}
              {item.scene_number ? (
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600 tabular-nums">
                  {item.scene_number}
                </span>
              ) : null}
            </div>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap flex gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
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
          ? 'border-green-200 bg-green-50/50'
          : 'border-red-200 bg-red-50/50'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <span className={`text-sm font-semibold ${block.passed ? 'text-green-800' : 'text-red-800'}`}>
          {block.detail || (block.passed ? '通过' : '未通过')}
        </span>
      </div>
      {(block.issues || []).length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {block.issues.map((issue, index) => (
            <li key={`issue-${index}`} className="rounded-lg bg-white/80 px-3 py-2 text-sm text-gray-700 leading-relaxed">
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
    <section className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div
        className={`px-4 py-4 border-b border-gray-100 ${
          block.passed ? 'bg-emerald-50/70' : 'bg-red-50/70'
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          {block.passed ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          ) : (
            <XCircle className="h-5 w-5 text-red-600" />
          )}
          <span
            className={`text-sm font-semibold ${
              block.passed ? 'text-emerald-800' : 'text-red-800'
            }`}
          >
            {block.passed ? '合规通过' : '合规未通过'}
          </span>
        </div>
        {block.conclusion ? (
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap pl-7">
            {block.conclusion}
          </p>
        ) : null}
      </div>

      {levels.length > 0 ? (
        <div className="p-4 border-b border-gray-100">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-3">
            三级风险扫描
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {levels.map((level) => (
              <article
                key={level.level}
                className={`rounded-xl border px-3.5 py-3 ${
                  level.passed
                    ? 'border-emerald-100 bg-emerald-50/40'
                    : 'border-amber-100 bg-amber-50/40'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className="text-sm font-semibold text-gray-900">{level.level}</p>
                  <span
                    className={`text-[11px] font-medium ${
                      level.passed ? 'text-emerald-700' : 'text-amber-700'
                    }`}
                  >
                    {level.status}
                  </span>
                </div>
                {level.detail ? (
                  <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap mt-1">
                    {level.detail}
                  </p>
                ) : null}
                {(level.items || []).length > 0 ? (
                  <ul className="mt-2 space-y-1.5">
                    {level.items.map((item, index) => (
                      <li
                        key={`${level.level}-risk-${index}`}
                        className="rounded-lg bg-white/80 border border-gray-100 px-2.5 py-2 text-xs text-gray-700 leading-relaxed"
                      >
                        {item.location ? (
                          <span className="font-medium text-gray-500 mr-1">{item.location}</span>
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
            <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
              九维风险扫描
            </p>
            <span
              className={`text-[11px] font-medium ${
                nine.passed ? 'text-emerald-700' : 'text-amber-700'
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
                      ? 'border-emerald-100 bg-emerald-50/50 text-emerald-800'
                      : 'border-amber-100 bg-amber-50/50 text-amber-800'
                  }`}
                >
                  <p className="font-medium">{dim.name}</p>
                  <p className="mt-0.5 opacity-80">{dim.status}</p>
                </div>
              ))}
            </div>
          ) : null}

          {nine.summary ? (
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap mb-2">
              {nine.summary}
            </p>
          ) : null}

          {(nine.items || []).length === 0 && !(nine.dimensions || []).length && !nine.summary ? (
            <p className="text-sm text-gray-500">未发现风险项</p>
          ) : null}

          {(nine.items || []).length > 0 ? (
            <ul className="space-y-2">
              {nine.items.map((item, index) => (
                <li
                  key={`nine-risk-${index}`}
                  className="rounded-lg border border-gray-100 bg-gray-50/60 px-3 py-2 text-sm text-gray-700 leading-relaxed"
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
      ? 'from-amber-400 to-yellow-500 text-white'
      : rating === 'A'
        ? 'from-indigo-500 to-violet-600 text-white'
        : 'from-gray-600 to-gray-700 text-white'

  const totalPercent =
    total != null && maxTotal ? Math.min(100, Math.round((Number(total) / maxTotal) * 100)) : null

  return (
    <section className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div className="px-5 py-5 bg-gradient-to-br from-slate-50 via-white to-indigo-50/40 border-b border-gray-100">
        <div className="flex flex-wrap items-end gap-4">
          {rating ? (
            <span
              className={`inline-flex h-14 min-w-[3.5rem] items-center justify-center rounded-2xl bg-gradient-to-br px-4 text-3xl font-black shadow-sm ${ratingStyle}`}
            >
              {rating}
            </span>
          ) : null}
          <div>
            {total != null ? (
              <p className="text-2xl font-bold text-gray-900 tabular-nums leading-none">
                {total}
                <span className="text-base font-medium text-gray-400"> / {maxTotal}</span>
              </p>
            ) : null}
            {totalPercent != null ? (
              <p className="mt-1 text-xs text-gray-500">综合得分 {totalPercent}%</p>
            ) : null}
          </div>
          {fuseTriggered === true ? (
            <span className="ml-auto rounded-lg border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
              已触发熔断
            </span>
          ) : fuseTriggered === false ? (
            <span className="ml-auto rounded-lg border border-emerald-100 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
              未触发熔断
            </span>
          ) : null}
        </div>
      </div>

      {dimensions.length > 0 ? (
        <div className="p-4 space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 px-1">
            八维评分
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
                percent == null ? 'bg-indigo-500' : percent >= 90 ? 'bg-emerald-500' : percent >= 75 ? 'bg-indigo-500' : 'bg-amber-500'

              return (
                <article
                  key={`${row.name}-${index}`}
                  className="rounded-xl border border-gray-100 bg-gray-50/50 px-3.5 py-3"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <p className="text-sm font-medium text-gray-800">{row.name}</p>
                    <p className="text-sm font-bold text-gray-900 tabular-nums shrink-0">
                      {row.score}
                      {maxScore != null ? (
                        <span className="text-xs font-medium text-gray-400"> / {maxScore}</span>
                      ) : null}
                    </p>
                  </div>
                  {percent != null ? (
                    <div className="h-1.5 rounded-full bg-gray-200/80 overflow-hidden mb-2">
                      <div
                        className={`h-full rounded-full transition-all ${barColor}`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  ) : null}
                  {row.detail ? (
                    <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">
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

function ScoreBoardBlock({ block }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        {block.grade ? (
          <span className="text-4xl font-bold text-indigo-600 leading-none">{block.grade}</span>
        ) : null}
        {block.total != null ? (
          <span className="text-sm text-gray-500 pb-1">总分 {block.total}</span>
        ) : null}
      </div>
      {block.summary ? (
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap border-l-2 border-indigo-100 pl-3">
          {block.summary}
        </p>
      ) : null}
      {(block.dimensions || []).length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {block.dimensions.map((row, index) => (
            <div
              key={`${row.name}-${index}`}
              className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2.5 text-sm"
            >
              <span className="text-gray-600">{row.name}</span>
              <span className="font-semibold text-gray-900 tabular-nums">{row.score}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  )
}

function ChecksBlock({ block }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm space-y-3">
      <div className="flex items-center gap-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <span className="text-sm font-semibold text-gray-900">{block.verdict || '—'}</span>
      </div>
      <div className="space-y-2">
        {(block.items || []).map((row, index) => (
          <div key={`${row.level}-${index}`} className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5">
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="font-medium text-gray-800">{row.level}</span>
              <span className="text-xs font-medium text-gray-500">{row.status}</span>
            </div>
            {row.detail ? (
              <p className="mt-1.5 text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{row.detail}</p>
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
    <div className="rounded-lg border border-gray-100 bg-gray-50/40 overflow-hidden">
      {showHeader && beat.sceneHeader ? (
        <div className="flex flex-wrap items-center gap-2 px-3 py-2 bg-white border-b border-gray-100">
          {sceneId ? (
            <span className="rounded-md bg-indigo-600 px-2 py-0.5 text-[11px] font-bold text-white tabular-nums">
              {sceneId}
            </span>
          ) : null}
          <span className="text-xs font-medium text-gray-600">{location || beat.sceneHeader}</span>
        </div>
      ) : null}

      <div className="px-3 py-2.5 space-y-2">
        {beat.action ? (
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap font-[family-name:var(--font-geist-mono,ui-monospace,monospace)]">
            {beat.action}
          </p>
        ) : null}

        {dialogue ? (
          <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 px-3 py-2.5">
            <p className="text-sm leading-relaxed text-gray-900">
              <span className="font-semibold text-indigo-800">{dialogue.speaker}</span>
              {dialogue.tone ? (
                <span className="text-xs text-indigo-500/90 ml-1">（{dialogue.tone}）</span>
              ) : null}
              <span className="text-gray-400 mx-1">：</span>
              <span>{dialogue.text}</span>
            </p>
          </div>
        ) : beat.dialogue ? (
          <p className="rounded-lg border border-indigo-100 bg-indigo-50/50 px-3 py-2.5 text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
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
      {/* 概览 */}
      <div className="rounded-xl border border-gray-200 bg-white px-4 py-3.5 shadow-sm flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
            <BookOpen className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-medium text-gray-400">剧本规模</p>
            <p className="text-sm font-semibold text-gray-900 tabular-nums">
              {block.total_episodes ?? episodes.length} 集 · {totalScenes} 场
            </p>
          </div>
        </div>
        {episodes.length > 1 ? (
          <div className="flex gap-2 text-xs ml-auto">
            <button type="button" onClick={expandAll} className="text-gray-500 hover:text-indigo-600 transition-colors">
              全部展开
            </button>
            <span className="text-gray-300">|</span>
            <button type="button" onClick={collapseAll} className="text-gray-500 hover:text-indigo-600 transition-colors">
              全部收起
            </button>
          </div>
        ) : null}
      </div>

      {/* 集数快速跳转（30 集时比纯滚动更高效） */}
      {episodes.length > 3 ? (
        <div className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 shadow-sm">
          <p className="text-[11px] font-medium text-gray-400 mb-2 px-1">快速跳转</p>
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
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                第{ep.episodeNumber}集
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {/* 分集列表（折叠阅读主体） */}
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
              className={`rounded-xl border bg-white overflow-hidden shadow-sm scroll-mt-4 transition-colors ${
                isActive ? 'border-indigo-300 ring-1 ring-indigo-100' : 'border-gray-200'
              }`}
            >
              <button
                type="button"
                onClick={() => toggleEpisode(epNo)}
                className="w-full flex items-center gap-3 px-4 py-3.5 text-left hover:bg-gray-50/80 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-gray-900">
                      第{epNo}集
                      {episode.title && episode.title !== `第${epNo}集` ? ` · ${episode.title}` : ''}
                    </p>
                    {sceneCount > 0 ? (
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-500">
                        {sceneCount} 场
                      </span>
                    ) : null}
                  </div>
                  {!isOpen && episode.memoryCheckPoint ? (
                    <p className="mt-1 text-xs text-gray-500 line-clamp-1">{episode.memoryCheckPoint}</p>
                  ) : null}
                </div>
                {isOpen ? (
                  <ChevronUp className="h-4 w-4 text-gray-400 shrink-0" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
                )}
              </button>

              {isOpen ? (
                <div className="px-4 pb-4 border-t border-gray-100 space-y-3">
                  {episode.memoryCheckPoint ? (
                    <div className="pt-3 rounded-lg bg-emerald-50/70 border border-emerald-100 px-3.5 py-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-700/90">
                        记忆检查点
                      </p>
                      <p className="mt-1.5 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {episode.memoryCheckPoint}
                      </p>
                    </div>
                  ) : null}

                  {visibleBeats.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
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
                    <p className="pt-3 text-sm text-gray-400 text-center py-6">暂无场次内容</p>
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
    <section className="rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50/60 via-white to-violet-50/40 overflow-hidden shadow-sm">
      {block.title ? (
        <div className="px-5 py-3 border-b border-indigo-100/80">
          <SectionTitle>{block.title}</SectionTitle>
        </div>
      ) : null}
      <div className="p-5 space-y-4">
        {block.hero_text ? (
          <p className="text-sm text-gray-800 leading-7 whitespace-pre-wrap">{block.hero_text}</p>
        ) : null}
        {hasMetrics ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {block.metrics.map((item, index) => (
              <div key={`${item.label}-${index}`} className="rounded-lg bg-white border border-gray-100 px-3 py-2.5">
                <p className="text-[11px] text-indigo-600">{item.label}</p>
                <p className="text-lg font-bold text-gray-900 mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        ) : null}
        {hasChecks ? (
          <div className="space-y-2">
            {block.checks.map((check, index) => (
              <div key={`check-${index}`} className="rounded-lg bg-white/80 border border-gray-100 px-3.5 py-3">
                <p className="text-xs font-semibold text-gray-600">{check.label}</p>
                <p className="mt-1 text-sm text-gray-800 leading-relaxed">{check.text}</p>
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
    <section className="space-y-4">
      <SectionTitle>角色档案</SectionTitle>
      {characters.map((char, index) => (
        <KvBlock
          key={`char-${index}`}
          block={{ title: char.title, rows: char.rows || [], layout: 'columns_2' }}
        />
      ))}
    </section>
  )
}

function RelationshipGraphBlock({ block }) {
  return <CardsBlock block={{ title: '关系网络', items: block.items || [], layout: 'stack' }} />
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
    <section className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
        <SectionTitle>{block.title}</SectionTitle>
        {passed === true ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
            <CheckCircle2 className="h-3.5 w-3.5" />通过
          </span>
        ) : passed === false ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700">
            <XCircle className="h-3.5 w-3.5" />未通过
          </span>
        ) : null}
      </div>
      <div className="p-5 space-y-4">
        {(block.metrics || []).length > 0 ? (
          <MetricsBlock block={{ items: block.metrics }} />
        ) : null}
        {block.detail ? (
          <p className="text-sm text-gray-800 leading-7 whitespace-pre-wrap">{block.detail}</p>
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
          <article key={`${ep.episode_no || index}`} className="rounded-xl border border-gray-200 bg-white px-4 py-3.5 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-gray-900">{ep.title}</p>
              {ep.subtitle ? (
                <span className="text-xs text-gray-500">{ep.subtitle}</span>
              ) : null}
            </div>
            {ep.body ? (
              <p className="mt-2 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap border-l-2 border-indigo-100 pl-3">
                {ep.body}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  )
}

function DeliverableSectionsBlock({ block }) {
  const sections = block.sections || []
  if (!sections.length) return null
  return (
    <section className="space-y-5">
      {block.title ? <SectionTitle>{block.title}</SectionTitle> : null}
      {sections.map((section, index) => {
        if (section.kind === 'metrics') {
          return <MetricsBlock key={`ds-${index}`} block={{ title: section.title, items: section.items }} />
        }
        if (section.kind === 'paragraph') {
          return <ParagraphBlock key={`ds-${index}`} block={{ title: section.title, text: section.text }} />
        }
        if (section.kind === 'list') {
          return <ListBlock key={`ds-${index}`} block={{ title: section.title, items: section.items || [] }} />
        }
        if (section.kind === 'kv') {
          return <KvBlock key={`ds-${index}`} block={{ title: section.title, rows: section.rows || [] }} />
        }
        return null
      })}
    </section>
  )
}

export function PresentationBlock({ block }) {
  if (!block) return null
  switch (block.type) {
    case 'hero':
      return <HeroBlock block={block} />
    case 'metrics':
      return <MetricsBlock block={block} />
    case 'kv':
      return <KvBlock block={block} />
    case 'paragraph':
      return <ParagraphBlock block={block} />
    case 'list':
      return <ListBlock block={block} />
    case 'outline_overview':
      return <OutlineOverviewBlock block={block} />
    case 'stage_outlines':
      return <StageOutlinesBlock block={block} />
    case 'cards':
      return <CardsBlock block={block} />
    case 'steps':
      return <StepsBlock block={block} />
    case 'review_overview':
      return <ReviewOverviewBlock block={block} />
    case 'review_issues':
      return <ReviewIssuesBlock block={block} />
    case 'verdict':
      return <VerdictBlock block={block} />
    case 'compliance_report':
      return <ComplianceReportBlock block={block} />
    case 'quality_report':
      return <QualityReportBlock block={block} />
    case 'score_board':
      return <ScoreBoardBlock block={block} />
    case 'checks':
      return <ChecksBlock block={block} />
    case 'script_episodes':
      return <ScriptEpisodesBlock block={block} />
    case 'plan_overview':
      return <PlanOverviewBlock block={block} />
    case 'plan_items':
      return <PlanItemsBlock block={block} />
    case 'character_roster':
      return <CharacterRosterBlock block={block} />
    case 'relationship_graph':
      return <RelationshipGraphBlock block={block} />
    case 'world_sections':
      return <WorldSectionsBlock block={block} />
    case 'assessment_report':
      return <AssessmentReportBlock block={block} />
    case 'episode_metrics_list':
      return <EpisodeMetricsListBlock block={block} />
    case 'deliverable_sections':
      return <DeliverableSectionsBlock block={block} />
    default:
      return null
  }
}

export function DramaPresentationCard({ view, raw }) {
  const [showRaw, setShowRaw] = useState(false)
  if (!view) return null

  return (
    <article className="overflow-hidden">
      <header className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600">
            <FileText className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h4 className="text-base font-semibold text-gray-900">{view.label || view.artifact_key}</h4>
            {view.summary ? (
              <p className="mt-1 text-sm text-gray-500 leading-relaxed">{view.summary}</p>
            ) : null}
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowRaw((value) => !value)}
          className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-800 transition-colors"
        >
          {showRaw ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {showRaw ? '收起原始数据' : '查看 JSON'}
        </button>
      </header>

      <div className="space-y-5 w-full max-w-none">
        {(view.blocks || []).map((block, index) => (
          <PresentationBlock key={`${view.artifact_key}-${block.type}-${index}`} block={block} />
        ))}
        {!view.blocks?.length ? (
          <p className="rounded-xl border border-dashed border-gray-200 py-10 text-center text-sm text-gray-400">
            暂无可读内容
          </p>
        ) : null}
        {showRaw && raw != null ? (
          <pre className="text-xs bg-slate-900 text-slate-100 rounded-xl p-4 overflow-auto max-h-96 whitespace-pre-wrap font-mono leading-relaxed">
            {JSON.stringify(raw, null, 2)}
          </pre>
        ) : null}
      </div>
    </article>
  )
}

export default function DramaPresentation({ views = {}, rawArtifacts = {} }) {
  const keys = Object.keys(views)
  const [activeKey, setActiveKey] = useState(keys[0] || '')

  if (!keys.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-400">
        <FileText className="h-10 w-10 mb-3 opacity-40" />
        <p className="text-sm">执行已完成，暂无展示内容</p>
      </div>
    )
  }

  const currentKey = keys.includes(activeKey) ? activeKey : keys[0]

  return (
    <div>
      {keys.length > 1 ? (
        <div className="flex flex-wrap gap-2 mb-5 pb-4 border-b border-gray-100">
          {keys.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveKey(key)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                currentKey === key
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {views[key]?.label || key}
            </button>
          ))}
        </div>
      ) : null}
      <DramaPresentationCard view={views[currentKey]} raw={rawArtifacts[currentKey]} />
    </div>
  )
}

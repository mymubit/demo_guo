import { EChart, formatRhythmEpisodeLabel } from '@/components/charts'
import { resolveThemeCodeLabel } from '@/utils/displayLabels'
import { MetaChip } from './MasterDetailLayout'

const ARC_LABELS = {
  openingSetup: '开篇建立',
  escalation: '矛盾升级',
  midpointTwist: '中段大反转',
  finalConfrontation: '最终对决',
  resolution: '结局余味',
}

function PanelBlock({ title, icon: Icon, children, className = '' }) {
  if (!children) return null
  return (
    <div className={`rounded-2xl border border-white/5 bg-slate-900/40 overflow-hidden ${className}`}>
      {title ? (
        <div className="border-b border-white/5 bg-slate-900/60 px-5 py-3 flex items-center gap-2">
          {Icon ? <Icon className="w-3.5 h-3.5 text-gold-400/70" /> : null}
          <span className="text-xs font-medium text-gold-400/85">{title}</span>
        </div>
      ) : null}
      <div className="p-5">{children}</div>
    </div>
  )
}

function IntensityBar({ level }) {
  const value = Number(level)
  if (!Number.isFinite(value)) return <span className="text-xs text-navy-400">—</span>
  const pct = Math.min(100, Math.max(0, value * 10))
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="h-1.5 w-20 rounded-full bg-slate-700/50 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-amber-600/70 via-gold-400/90 to-gold-200"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[11px] text-gold-400/90 tabular-nums font-medium">{value}/10</span>
    </div>
  )
}

function parseEventLabel(event, index) {
  const text = String(event || '').trim()
  const matched = text.match(/^(Ep\d+|第\s*\d+\s*集)[:：\s-]+(.+)$/i)
  if (!matched) {
    return {
      label: String(index + 1).padStart(2, '0'),
      content: text,
    }
  }

  return {
    label: matched[1].replace(/\s+/g, ''),
    content: matched[2].trim(),
  }
}

export function RhythmBeatList({ blocks = [], editMode, inputClass, onUpdateBlock, onUpdateEvents }) {
  if (!blocks.length) return null

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/40 overflow-hidden divide-y divide-white/5">
      {blocks.map((block, index) => {
        const rangeKey = block.episodeRange || block.episodeGroup || block.episodeStart || index
        const events = block.keyEvents || []

        return (
          <div
            key={rangeKey}
            className="flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-5 px-4 py-4 transition-colors hover:bg-white/[0.03]"
          >
            <div className="sm:w-28 shrink-0">
              <div className="text-sm font-semibold text-white">
                {formatRhythmEpisodeLabel(block)}
              </div>
              <IntensityBar level={block.intensityLevel} />
            </div>

            <div className="flex-1 min-w-0 space-y-2">
              {editMode ? (
                <>
                  <div>
                    <div className="text-xs text-navy-400 mb-1">关键事件（每行一条）</div>
                    <textarea
                      value={events.join('\n')}
                      onChange={(e) => onUpdateEvents?.(block.episodeRange, e.target.value)}
                      rows={3}
                      className={inputClass}
                    />
                  </div>
                  <textarea
                    value={block.notes || ''}
                    onChange={(e) => onUpdateBlock?.(block.episodeRange, 'notes', e.target.value)}
                    rows={2}
                    placeholder="节奏说明"
                    className={inputClass}
                  />
                </>
              ) : (
                <>
                  {events.length > 0 && (
                    <ol className="space-y-2">
                      {events.map((event, i) => {
                        const item = parseEventLabel(event, i)
                        return (
                          <li
                            key={i}
                            className="flex gap-2.5 rounded-xl border border-white/5 bg-white/[0.025] px-3 py-2.5"
                          >
                            <span className="mt-0.5 inline-flex h-5 min-w-8 shrink-0 items-center justify-center rounded-md border border-gold-400/20 bg-gold-400/10 px-1.5 text-[10px] font-semibold text-gold-300">
                              {item.label}
                            </span>
                            <span className="min-w-0 text-xs leading-relaxed text-navy-100">
                              {item.content}
                            </span>
                          </li>
                        )
                      })}
                    </ol>
                  )}
                  {(block.linkedReversals || []).length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] text-navy-400 shrink-0">段内反转</span>
                      {block.linkedReversals.map((rev) => (
                        <MetaChip key={rev.episodeNumber} className="text-cyan-300/90">
                          第 {rev.episodeNumber} 集
                        </MetaChip>
                      ))}
                    </div>
                  )}
                  {block.notes && (
                    <p className="text-xs text-navy-400 leading-relaxed">{block.notes}</p>
                  )}
                </>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

const REVERSAL_TONE = {
  '身份揭晓': 'border-violet-400/30 bg-violet-500/10 text-violet-200',
  '关系反转': 'border-pink-400/30 bg-pink-500/10 text-pink-200',
  '命运反转': 'border-amber-400/30 bg-amber-500/10 text-amber-200',
  '隐藏真相': 'border-cyan-400/30 bg-cyan-500/10 text-cyan-200',
  '反派反转': 'border-red-400/30 bg-red-500/10 text-red-200',
  '动机转变': 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
}

function reversalToneClass(label) {
  return REVERSAL_TONE[label] || 'border-white/10 bg-white/[0.03] text-navy-200'
}

export function ReversalTimeline({ points = [], editMode, inputClass, onUpdateReversal }) {
  if (!points.length) return null

  const sorted = [...points].sort(
    (a, b) => Number(a.episodeNumber || 0) - Number(b.episodeNumber || 0)
  )

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/40 px-4 py-5">
      <div className="relative space-y-0">
        {sorted.map((rev, index) => {
          const isLast = index === sorted.length - 1
          const typeLabel = rev.reversalTypeLabel || rev.reversalType || '其他'

          return (
            <div key={`${rev.episodeNumber}-${index}`} className="relative flex gap-4 pb-6 last:pb-0">
              {!isLast && (
                <span
                  className="absolute left-[11px] top-6 bottom-0 w-px bg-gradient-to-b from-gold-400/40 to-white/10"
                  aria-hidden
                />
              )}
              <div className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-gold-400/50 bg-slate-950 text-[10px] font-bold text-gold-300">
                {rev.episodeNumber}
              </div>
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className="text-sm font-medium text-white">第 {rev.episodeNumber} 集</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border ${reversalToneClass(typeLabel)}`}
                  >
                    {typeLabel}
                  </span>
                  {(rev.foreshadowEpisodes || []).length > 0 && (
                    <MetaChip>伏笔 E{rev.foreshadowEpisodes.join('、E')}</MetaChip>
                  )}
                </div>
                {editMode ? (
                  <textarea
                    value={rev.description || ''}
                    onChange={(e) => onUpdateReversal?.(rev.episodeNumber, 'description', e.target.value)}
                    rows={3}
                    className={inputClass}
                  />
                ) : (
                  <p className="text-sm text-navy-100 leading-relaxed">{rev.description}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function StructureMetaStrip({ items = [] }) {
  const visible = items.filter(Boolean)
  if (!visible.length) return null

  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-navy-400">
      {visible.map((text, i) => (
        <span key={text} className="inline-flex items-center gap-2">
          {i > 0 && <span className="text-navy-500 select-none">·</span>}
          <span>{text}</span>
        </span>
      ))}
    </div>
  )
}

export function hasWorldviewContent(worldview = {}) {
  const wv = worldview || {}
  return Boolean(
    String(wv.settingSummary || '').trim() ||
      (wv.rootRules || []).some((rule) => String(rule || '').trim()) ||
      (wv.coreNouns || []).length ||
      (wv.subWorldConsistency || []).some((item) => String(item?.text || '').trim()) ||
      String(wv.timePeriod || '').trim() ||
      String(wv.locationTypeLabel || '').trim()
  )
}

export function WorldviewPanel({
  worldview = {},
  validationLog,
  validationIssues = [],
  editMode,
  inputClass,
  onUpdateField,
  onUpdateRootRules,
}) {
  const wv = worldview
  const nouns = wv.coreNouns || []
  const rules = wv.rootRules || []
  const subWorld = wv.subWorldConsistency || []
  const hasContent = hasWorldviewContent(wv)
  const showValidation =
    validationLog && !validationLog.skipped && (validationLog.passed || validationIssues.length > 0)

  if (!editMode && !hasContent && !showValidation && validationIssues.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-navy-400 space-y-2">
        <p>暂无世界观生成内容</p>
        <p className="text-xs text-navy-400">请使用「重新生成」，或切换「编辑」手动填写</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {validationIssues.length > 0 ? (
        <ul className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs text-amber-100/90 space-y-1 list-disc list-inside">
          {validationIssues.slice(0, 5).map((issue, i) => (
            <li key={`world-validation-${i}`}>{issue}</li>
          ))}
        </ul>
      ) : null}

      {(wv.timePeriod || wv.locationTypeLabel) && !editMode && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-3">
          {wv.timePeriod ? (
            <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
              <div className="text-[10px] text-navy-400 mb-1">时代背景</div>
              <div className="text-sm text-white leading-snug">{wv.timePeriod}</div>
            </div>
          ) : null}
          {wv.locationTypeLabel ? (
            <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
              <div className="text-[10px] text-navy-400 mb-1">主要场景</div>
              <div className="text-sm text-white leading-snug">{wv.locationTypeLabel}</div>
            </div>
          ) : null}
        </div>
      )}

      {editMode ? (
        <div className="space-y-3 rounded-2xl border border-white/5 bg-slate-900/40 p-4">
          <div>
            <div className="text-xs text-navy-400 mb-1">时代背景</div>
            <input
              type="text"
              value={wv.timePeriod || ''}
              onChange={(e) => onUpdateField?.('timePeriod', e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <div className="text-xs text-navy-400 mb-1">世界观概述</div>
            <textarea
              value={wv.settingSummary || ''}
              onChange={(e) => onUpdateField?.('settingSummary', e.target.value)}
              rows={5}
              className={inputClass}
            />
          </div>
          <div>
            <div className="text-xs text-navy-400 mb-1">根法则（每行一条）</div>
            <textarea
              value={rules.join('\n')}
              onChange={(e) => onUpdateRootRules?.(e.target.value)}
              rows={4}
              className={inputClass}
            />
          </div>
        </div>
      ) : (
        <>
          {wv.settingSummary ? (
            <div className="rounded-2xl border border-gold-400/15 bg-gradient-to-br from-gold-400/8 via-navy-950/20 to-transparent border-l-4 border-l-gold-400/45 px-5 py-5">
              <div className="text-xs font-medium text-gold-400/90 mb-2">造梦师全景地图</div>
              <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">
                {wv.settingSummary}
              </p>
            </div>
          ) : null}

          {rules.length > 0 ? (
            <PanelBlock title="根法则与第一铁律">
              <div className="space-y-3">
                {rules.map((rule, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span
                      className={`shrink-0 mt-0.5 text-[10px] px-2 py-0.5 rounded-full border ${
                        i === 0
                          ? 'border-gold-400/35 bg-gold-400/12 text-gold-300'
                          : 'border-white/10 bg-white/[0.03] text-slate-400'
                      }`}
                    >
                      {i === 0 ? '第一铁律' : `法则 ${i + 1}`}
                    </span>
                    <p className="text-sm text-navy-100 leading-relaxed flex-1">{rule}</p>
                  </div>
                ))}
              </div>
            </PanelBlock>
          ) : null}
        </>
      )}

      {nouns.length > 0 ? (
        <PanelBlock title="核心名词表">
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-3">
            {nouns.map((n, i) => (
              <div
                key={i}
                className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-4 hover:border-white/20 transition-colors"
              >
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <div className="text-sm font-medium text-gold-400/90">{n.term}</div>
                  {n.tierLabel ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-slate-400">
                      {n.tierLabel}
                    </span>
                  ) : null}
                </div>
                <p className="text-xs text-navy-300 leading-relaxed mt-1.5">{n.definition}</p>
              </div>
            ))}
          </div>
        </PanelBlock>
      ) : null}

      {subWorld.length > 0 && !editMode ? (
        <PanelBlock title="设定维度">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {subWorld.map((item) => (
              <div
                key={item.key}
                className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3"
              >
                <div className="text-xs font-medium text-gold-400/80">{item.label}</div>
                <p className="text-sm text-navy-200 leading-relaxed mt-1.5">{item.text}</p>
              </div>
            ))}
          </div>
        </PanelBlock>
      ) : null}
    </div>
  )
}

function StoryArcFlow({ arc = {}, editMode, inputClass, onUpdateArc }) {
  const entries = Object.entries(ARC_LABELS).filter(([key]) => editMode || arc[key])

  if (!entries.length) return null

  return (
    <PanelBlock title="核心故事弧">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {entries.map(([key, label], index) => (
          <div key={key} className="relative">
            {index > 0 ? (
              <span
                className="hidden md:block absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-px bg-gold-400/30"
                aria-hidden
              />
            ) : null}
            <div className="h-full rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3">
              <div className="text-[10px] font-medium text-gold-400/85 mb-2">{label}</div>
              {editMode ? (
                <textarea
                  value={arc[key] || ''}
                  onChange={(e) => onUpdateArc?.(key, e.target.value)}
                  rows={3}
                  className={inputClass}
                />
              ) : (
                <p className="text-xs text-navy-100 leading-relaxed line-clamp-6">{arc[key]}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </PanelBlock>
  )
}

function StageTimeline({ stages = [], editMode, inputClass, onUpdateStage }) {
  if (!stages.length) return null

  return (
    <PanelBlock title="六阶段结构">
      <div className="space-y-0">
        {stages.map((stage, index) => {
          const isLast = index === stages.length - 1
          const episodeLabel = stage.episodeRange
            ? `第 ${stage.episodeRange} 集`
            : stage.startEpisode != null
              ? `第 ${stage.startEpisode}-${stage.endEpisode} 集`
              : ''

          return (
            <div key={stage.stageIndex || stage.stageName} className="relative flex gap-4 pb-5 last:pb-0">
              {!isLast ? (
                <span
                  className="absolute left-[15px] top-8 bottom-0 w-px bg-gradient-to-b from-gold-400/35 to-white/10"
                  aria-hidden
                />
              ) : null}
              <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-gold-400/45 bg-slate-950 text-xs font-bold text-gold-300">
                {stage.stageIndex}
              </div>
              <div className="flex-1 min-w-0 rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div>
                    <span className="text-sm font-semibold text-white">{stage.stageName}</span>
                    {stage.primaryTheme && !editMode ? (
                      <p className="text-[11px] text-gold-400/75 mt-0.5">{stage.primaryTheme}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    {episodeLabel ? (
                      <span className="px-2 py-0.5 rounded-full border border-white/10 text-navy-300">
                        {episodeLabel}
                      </span>
                    ) : null}
                    {stage.intensityMin != null ? (
                      <span className="px-2 py-0.5 rounded-full border border-amber-500/25 text-amber-200/90">
                        情绪 {stage.intensityMin}-{stage.intensityMax}
                      </span>
                    ) : null}
                    {stage.keyReversalCount != null ? (
                      <span className="px-2 py-0.5 rounded-full border border-pink-500/20 text-pink-200/80">
                        {stage.keyReversalCount} 反转
                      </span>
                    ) : null}
                  </div>
                </div>
                {editMode ? (
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={stage.stageName || ''}
                      onChange={(e) => onUpdateStage?.(stage.stageIndex, 'stageName', e.target.value)}
                      placeholder="阶段名称"
                      className={inputClass}
                    />
                    <input
                      type="text"
                      value={stage.primaryTheme || ''}
                      onChange={(e) => onUpdateStage?.(stage.stageIndex, 'primaryTheme', e.target.value)}
                      placeholder="阶段主题"
                      className={inputClass}
                    />
                    <textarea
                      value={stage.coreTask || ''}
                      onChange={(e) => onUpdateStage?.(stage.stageIndex, 'coreTask', e.target.value)}
                      rows={3}
                      className={inputClass}
                    />
                  </div>
                ) : (
                  <p className="text-sm text-navy-100 leading-relaxed">{stage.coreTask}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </PanelBlock>
  )
}

export function ActStructureSummary({ actStructure = {} }) {
  const actCount = actStructure.actCount
  const themeLabel = resolveThemeCodeLabel(actStructure.themeCode, actStructure.themeCodeLabel)
  const points = actStructure.reversalPoints || []
  if (!actCount && !themeLabel && !points.length) return null

  return (
    <div>
      <div className="text-xs font-medium text-gold-300 mb-2">幕结构</div>
      <div className="flex flex-wrap gap-2 mb-3">
        {actCount != null && <MetaChip>{actCount} 幕</MetaChip>}
        {themeLabel ? <MetaChip>主题 {themeLabel}</MetaChip> : null}
      </div>
      {points.length > 0 ? (
        <div className="space-y-2">
          {points.map((point, i) => (
            <div
              key={`${point.label}-${i}`}
              className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2.5"
            >
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="text-sm font-medium text-white">{point.label || `反转 ${i + 1}`}</span>
                {point.episode != null ? (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-slate-400">
                    第 {point.episode} 集
                  </span>
                ) : null}
              </div>
              {point.description ? (
                <p className="text-xs text-navy-300 leading-relaxed">{point.description}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function StoryStructurePanel({
  arc = {},
  stages = [],
  sankeyOption,
  sankeyHeight = 320,
  editMode,
  inputClass,
  onUpdateArc,
  onUpdateStage,
}) {
  return (
    <div className="space-y-4">
      {sankeyOption ? (
        <div className="rounded-2xl border border-white/5 bg-slate-900/40 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2 px-1">
            <div className="text-xs text-navy-400">结构流向 · 阶段 → 节奏 → 反转</div>
            <div className="flex flex-wrap gap-3 text-[10px] text-navy-400">
              <span className="inline-flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-[#d4a853]" />
                阶段
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-[#8b7ec8]" />
                节奏
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-[#e879a8]" />
                反转
              </span>
            </div>
          </div>
          <EChart option={sankeyOption} height={sankeyHeight} />
        </div>
      ) : null}

      <StoryArcFlow
        arc={arc}
        editMode={editMode}
        inputClass={inputClass}
        onUpdateArc={onUpdateArc}
      />

      <StageTimeline
        stages={stages}
        editMode={editMode}
        inputClass={inputClass}
        onUpdateStage={onUpdateStage}
      />
    </div>
  )
}

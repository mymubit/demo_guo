import { Loader2, Sparkles } from 'lucide-react'
import { MetaChip } from './MasterDetailLayout'
import PlotFlowChart from './PlotFlowChart'
import { isEnglishSlug, resolveHookLabel, resolveReversalLabel } from '@/utils/displayLabels'

export const SUMMARY_MIN = 100
export const SUMMARY_MAX = 200

export const KEY_EPISODE_TYPES = [
  { value: '', label: '非关键集' },
  { value: 'big-reversal', label: '大反转' },
  { value: 'climax', label: '高潮' },
  { value: 'emotional-peak', label: '情绪峰值' },
  { value: 'identity-reveal', label: '身份揭露' },
  { value: 'confrontation', label: '对峙' },
  { value: 'setup', label: '铺垫' },
  { value: 'not-key', label: '普通集' },
]

const KEY_EPISODE_TYPE_LABELS = Object.fromEntries(
  KEY_EPISODE_TYPES.filter((t) => t.value).map((t) => [t.value, t.label])
)

const REVERSAL_INTENSITY_LABELS = {
  minor: '小反转',
  major: '大反转',
  climax: '高潮反转',
}

const REVERSAL_TYPE_LABELS = {
  'identity-reveal': '身份揭晓',
  'relationship-reversal': '关系反转',
  'fortunes-reversal': '命运反转',
  'hidden-truth': '隐藏真相',
  'villain-twist': '反派反转',
  'motivation-change': '动机转变',
  other: '其他',
}

const PAYWALL_MARKER_LABELS = {
  paywall: '付费卡点',
  'strong-hook': '强钩子',
  cliffhanger: '悬念卡点',
}

export function blockRange(block) {
  return {
    from: block?.from_episode ?? block?.fromEpisode ?? 1,
    to: block?.to_episode ?? block?.toEpisode ?? 1,
  }
}

function episodePreview(ep) {
  const summary = (ep.oneLineSummary || '').trim()
  if (summary.length >= 40) return `${summary.slice(0, 40)}…`
  return summary || ep.title || '已填充'
}

function resolveKeyEpisodeTypeLabel(type) {
  if (!type) return ''
  return KEY_EPISODE_TYPE_LABELS[type] || (isEnglishSlug(type) ? '' : type)
}

function formatReversalLine(rev) {
  const parts = [`第${rev.episode}集`]
  const typeLabel =
    rev.typeLabel ||
    REVERSAL_TYPE_LABELS[rev.type] ||
    REVERSAL_TYPE_LABELS[rev.reversalType] ||
    (rev.type && !isEnglishSlug(rev.type) ? rev.type : '') ||
    (rev.reversalType && !isEnglishSlug(rev.reversalType) ? rev.reversalType : '')
  if (typeLabel) parts.push(typeLabel)
  if (rev.techniqueLabel) parts.push(rev.techniqueLabel)
  if (rev.patternName) parts.push(rev.patternName)
  if (rev.intensity) {
    parts.push(REVERSAL_INTENSITY_LABELS[rev.intensity] || rev.intensity)
  }
  if (rev.setupEpisode) parts.push(`铺垫第${rev.setupEpisode}集`)
  const detail = rev.note || rev.description || ''
  return detail ? `${parts.join(' · ')}：${detail}` : parts.join(' · ')
}

export function hasPortalPlanningContent(draft) {
  const cp = draft?.creativePlan || {}
  const keyHighlights = draft?.keyHighlights || []
  return (
    keyHighlights.length > 0 ||
    (cp.paymentCheckpoints || []).length > 0 ||
    (cp.reversalSchedule || []).length > 0 ||
    !!(cp.pacingNotes || '').trim() ||
    !!(cp.conflictStrategy?.antagonistPressure || '').trim()
  )
}

export function buildOutlineNavSections(draft) {
  const sections = [{ id: 'overview', label: '总览', subtitle: '脉络与关键集' }]

  if (hasPortalPlanningContent(draft)) {
    sections.push({ id: 'planning', label: '创作规划', subtitle: '亮点与节奏' })
  }

  const blocks = draft?.stageBlocks || draft?.navigation || []
  for (const block of blocks) {
    const { from, to } = blockRange(block)
    sections.push({
      id: `stage-${block.key}`,
      label: block.label || '阶段',
      subtitle: `第 ${from}-${to} 集`,
      stageKey: block.key,
    })
  }

  return sections
}

export function looksLikeEpisodeDump(text) {
  const t = String(text || '').trim()
  if (!t) return false
  const markers = t.match(/(?:Ep\s*\d+|第\s*\d+\s*集|Ep\d+)/gi) || []
  return markers.length >= 2
}

export function stageDirectionText(block) {
  const core = String(block?.coreTask || '').trim()
  const rough = String(block?.roughOutline || '').trim()
  if (looksLikeEpisodeDump(rough)) {
    if (core) return core
    const firstBlock = rough.split(/\n{2,}/)[0]?.trim() || ''
    return firstBlock.length > 280 ? `${firstBlock.slice(0, 280)}…` : firstBlock
  }
  if (rough.length <= 420) return rough
  return `${rough.slice(0, 420)}…`
}

export function getStageGenerationState(block, episodes = []) {
  const { from, to } = blockRange(block)
  const direction = stageDirectionText(block)
  const roughReady = direction.length >= 20 || String(block?.coreTask || '').trim().length >= 10
  let nextEp = null
  let pendingCount = 0
  for (let n = from; n <= to; n += 1) {
    const ep = episodes.find((e) => e.episodeNumber === n)
    if (!ep?.filled) {
      pendingCount += 1
      if (nextEp == null) nextEp = n
    }
  }
  return { from, to, roughReady, nextEp, pendingCount, totalInStage: to - from + 1 }
}

export function OutlineMetaStrip({ draft }) {
  const eps = draft?.episodes || []
  const total = draft?.totalEpisodes || eps.length || 0
  const filledCount = eps.filter((e) => e.filled).length

  return (
    <div className="flex flex-wrap items-center gap-2">
      <MetaChip>{total} 集</MetaChip>
      <MetaChip>已填充 {filledCount} 集</MetaChip>
      {!draft?.frameworkReady && <MetaChip>阶段待规划</MetaChip>}
    </div>
  )
}

export function OutlineSummaryBanner({ summary, editMode, onChange, inputClass }) {
  if (!summary && !editMode) return null
  const textareaClass =
    inputClass ||
    'w-full rounded-xl bg-navy-950/50 border border-navy-600/30 text-white text-sm px-4 py-3 focus:border-gold-400/50 outline-none resize-y'

  return (
    <div className="rounded-xl border border-navy-700/35 bg-navy-900/45 px-4 py-3.5">
      <div className="text-[10px] text-gold-400/70 font-medium mb-1.5 tracking-wide">整体结构总结</div>
      {editMode ? (
        <textarea
          value={summary || ''}
          onChange={(e) => onChange?.(e.target.value)}
          rows={4}
          className={textareaClass}
          placeholder="全剧脉络：主线推进、阶段转折与情感高潮"
        />
      ) : (
        <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{summary}</p>
      )}
    </div>
  )
}

function PlanBlock({ title, children }) {
  if (!children) return null
  return (
    <div>
      <div className="text-xs text-gold-400/80 font-medium mb-2">{title}</div>
      {children}
    </div>
  )
}

export function OutlinePlanningPanel({ draft }) {
  const cp = draft?.creativePlan || {}
  const keyHighlights = draft?.keyHighlights || []
  const antagonistPressure = (cp.conflictStrategy?.antagonistPressure || '').trim()

  if (!hasPortalPlanningContent(draft)) {
    return (
      <p className="text-sm text-navy-400 text-center py-8">暂无创作规划内容</p>
    )
  }

  return (
    <div className="space-y-5">
      {keyHighlights.length > 0 && (
        <PlanBlock title="关键亮点">
          <ul className="text-sm text-navy-100 space-y-2">
            {keyHighlights.map((hl, i) => (
              <li key={`hl-${i}`} className="leading-relaxed">
                <span className="text-gold-400/90">第{hl.episode || hl.episodeNumber}集</span>
                {(hl.title || hl.description) && (
                  <span className="text-navy-100"> · {hl.title || hl.description}</span>
                )}
              </li>
            ))}
          </ul>
        </PlanBlock>
      )}

      {antagonistPressure && (
        <PlanBlock title="反派压力线">
          <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{antagonistPressure}</p>
        </PlanBlock>
      )}

      {(cp.paymentCheckpoints || []).length > 0 && (
        <PlanBlock title="付费卡点">
          <ul className="text-sm text-navy-100 space-y-1.5">
            {cp.paymentCheckpoints.map((pt, i) => {
              const markerLabel = pt.markerLabel || PAYWALL_MARKER_LABELS[pt.marker] || pt.marker
              const marker =
                markerLabel && !isEnglishSlug(markerLabel) ? markerLabel : PAYWALL_MARKER_LABELS[pt.marker] || ''
              return (
                <li key={`pay-${i}`}>
                  第{pt.episode}集
                  {marker ? ` · ${marker}` : ''}
                  {pt.description ? ` · ${pt.description}` : ''}
                </li>
              )
            })}
          </ul>
        </PlanBlock>
      )}

      {(cp.reversalSchedule || []).length > 0 && (
        <PlanBlock title="反转排期">
          <ul className="text-sm text-navy-100 space-y-1.5">
            {cp.reversalSchedule.map((rev, i) => (
              <li key={`rev-${i}`}>{formatReversalLine(rev)}</li>
            ))}
          </ul>
        </PlanBlock>
      )}

      {cp.pacingNotes && (
        <PlanBlock title="节奏备注">
          <p className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed">{cp.pacingNotes}</p>
        </PlanBlock>
      )}
    </div>
  )
}

export function OutlineOverviewPanel({ draft, onJumpToEpisode }) {
  const stageBlocks = draft?.stageBlocks || draft?.navigation || []
  const eps = draft?.episodes || []
  const keyEpisodeIndex = draft?.keyEpisodeIndex || []
  const showPlotFlow = stageBlocks.length > 0 || eps.some((e) => e.filled)

  const keyEps = keyEpisodeIndex
    .map((num) => eps.find((e) => e.episodeNumber === num))
    .filter(Boolean)

  return (
    <div className="space-y-5">
      {showPlotFlow ? (
        <PlotFlowChart stageBlocks={stageBlocks} episodes={eps} height={340} />
      ) : (
        <p className="text-sm text-navy-400 text-center py-6">生成阶段粗纲或分集后将展示剧情脉络图</p>
      )}

      {keyEpisodeIndex.length > 0 && (
        <div>
          <div className="text-xs text-gold-400/80 font-medium mb-2">关键集索引</div>
          <div className="flex flex-wrap gap-2">
            {keyEpisodeIndex.map((epNum) => {
              const ep = eps.find((e) => e.episodeNumber === epNum)
              const typeLabel = resolveKeyEpisodeTypeLabel(ep?.keyEpisodeType)
              return (
                <button
                  key={epNum}
                  type="button"
                  onClick={() => onJumpToEpisode?.(epNum)}
                  className="inline-flex items-center gap-1 rounded-lg border border-navy-600/40 bg-navy-900/50 px-2.5 py-1 text-xs text-navy-200 hover:border-gold-400/40 hover:bg-gold-400/10 transition-colors"
                >
                  第 {epNum} 集
                  {typeLabel ? <span className="text-navy-500">· {typeLabel}</span> : null}
                  {ep?.title ? <span className="text-navy-400 truncate max-w-[120px]">· {ep.title}</span> : null}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {keyEps.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs text-gold-400/80 font-medium">关键集梗概</div>
          {keyEps.map((ep) => (
            <OutlineEpisodeCard key={ep.episodeNumber} ep={ep} compact />
          ))}
        </div>
      )}
    </div>
  )
}

function FieldLabel({ children, hint }) {
  return (
    <div className="flex items-center justify-between gap-2 mb-1">
      <span className="text-xs text-navy-500">{children}</span>
      {hint && <span className="text-[10px] text-navy-600">{hint}</span>}
    </div>
  )
}

function ReadonlyField({ label, value, multiline }) {
  if (value === null || value === undefined || value === '') return null
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      {multiline ? (
        <p className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed">{value}</p>
      ) : (
        <p className="text-sm text-navy-100">{value}</p>
      )}
    </div>
  )
}

export function OutlineEpisodeCard({ ep, compact = false }) {
  if (!ep?.filled) return null
  const stageName = ep.stageInfo?.stageName
  const chars = (ep.keyCharacters || []).join('、')
  const typeLabel = resolveKeyEpisodeTypeLabel(ep.keyEpisodeType)

  return (
    <div
      className={`rounded-xl bg-navy-900/40 border border-navy-700/30 ${
        compact ? 'p-3 space-y-2' : 'p-4 space-y-3'
      }`}
    >
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-white text-sm font-medium">第 {ep.episodeNumber} 集</span>
        {ep.title && <span className="text-sm text-navy-200">{ep.title}</span>}
        {stageName && <MetaChip>{stageName}</MetaChip>}
        {ep.emotionalIntensity != null && <MetaChip>情绪 {ep.emotionalIntensity}/10</MetaChip>}
        {ep.sceneCount != null && <MetaChip>{ep.sceneCount} 场</MetaChip>}
        {ep.isKeyEpisode && <MetaChip>关键集</MetaChip>}
        {typeLabel && <MetaChip>{typeLabel}</MetaChip>}
        {resolveHookLabel(ep) ? (
          <MetaChip title={ep.hookTypeHint}>{resolveHookLabel(ep)}</MetaChip>
        ) : null}
        {resolveReversalLabel(ep) ? (
          <MetaChip title={ep.reversalPatternHint}>{resolveReversalLabel(ep)}</MetaChip>
        ) : null}
      </div>
      <ReadonlyField label="本集梗概" value={ep.oneLineSummary} multiline />
      {!compact && (
        <>
          <ReadonlyField label="开头钩子" value={ep.hook} multiline />
          <ReadonlyField label="本集反转" value={ep.reversal} multiline />
          <ReadonlyField label="结尾悬念" value={ep.cliffhanger} multiline />
          <ReadonlyField label="主要角色" value={chars} />
          <ReadonlyField label="备注" value={ep.notes} multiline />
        </>
      )}
    </div>
  )
}

export function OutlineEpisodeDetail({
  ep,
  editMode,
  inputClass,
  onUpdateEpisode,
  onUpdateKeyCharacters,
}) {
  if (!ep) return null

  if (!ep.filled && !editMode) {
    return (
      <p className="text-sm text-navy-400 text-center py-4">
        第 {ep.episodeNumber} 集尚未生成，请使用上方「生成下一集」
      </p>
    )
  }

  const summaryLen = (ep.oneLineSummary || '').length

  if (editMode) {
    return (
      <div className="space-y-3">
        <div>
          <FieldLabel hint={`${(ep.title || '').length} / 30`}>集标题</FieldLabel>
          <input
            type="text"
            value={ep.title || ''}
            maxLength={30}
            onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'title', e.target.value)}
            placeholder="本集小标题"
            className={inputClass}
          />
        </div>
        <div>
          <FieldLabel hint={`${summaryLen} / ${SUMMARY_MAX}（至少 ${SUMMARY_MIN} 字）`}>本集梗概</FieldLabel>
          <textarea
            value={ep.oneLineSummary || ''}
            onChange={(e) =>
              onUpdateEpisode(ep.episodeNumber, 'oneLineSummary', e.target.value.slice(0, SUMMARY_MAX))
            }
            rows={6}
            maxLength={SUMMARY_MAX}
            placeholder={`${SUMMARY_MIN}-${SUMMARY_MAX} 字，写清本集核心动作与结果`}
            className={inputClass}
          />
        </div>
        <div>
          <FieldLabel>开头钩子</FieldLabel>
          <textarea
            value={ep.hook || ''}
            onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'hook', e.target.value.slice(0, 200))}
            rows={3}
            maxLength={200}
            placeholder="3-5 秒内触发疑问/张力的具体画面或台词"
            className={inputClass}
          />
        </div>
        <div>
          <FieldLabel>本集反转</FieldLabel>
          <textarea
            value={ep.reversal || ''}
            onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'reversal', e.target.value.slice(0, 200))}
            rows={3}
            maxLength={200}
            className={inputClass}
          />
        </div>
        <div>
          <FieldLabel>结尾悬念</FieldLabel>
          <textarea
            value={ep.cliffhanger || ''}
            onChange={(e) =>
              onUpdateEpisode(ep.episodeNumber, 'cliffhanger', e.target.value.slice(0, 200))
            }
            rows={3}
            maxLength={200}
            className={inputClass}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FieldLabel>情绪强度 (1-10)</FieldLabel>
            <input
              type="number"
              min={1}
              max={10}
              value={ep.emotionalIntensity ?? ''}
              onChange={(e) =>
                onUpdateEpisode(
                  ep.episodeNumber,
                  'emotionalIntensity',
                  e.target.value === '' ? null : Number(e.target.value)
                )
              }
              className={inputClass}
            />
          </div>
          <div>
            <FieldLabel>场景数 (1-3)</FieldLabel>
            <input
              type="number"
              min={1}
              max={3}
              value={ep.sceneCount ?? ''}
              onChange={(e) =>
                onUpdateEpisode(
                  ep.episodeNumber,
                  'sceneCount',
                  e.target.value === '' ? null : Number(e.target.value)
                )
              }
              className={inputClass}
            />
          </div>
        </div>
        <div>
          <FieldLabel>主要角色（逗号或顿号分隔，最多 5 人）</FieldLabel>
          <input
            type="text"
            value={(ep.keyCharacters || []).join('、')}
            onChange={(e) => onUpdateKeyCharacters(ep.episodeNumber, e.target.value)}
            className={inputClass}
          />
        </div>
        <details className="rounded-xl border border-navy-700/30 bg-navy-950/30 px-3 py-2">
          <summary className="text-xs text-navy-500 cursor-pointer select-none">高级字段</summary>
          <div className="mt-3 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <FieldLabel>钩子编码</FieldLabel>
                <input
                  type="text"
                  value={ep.hookTypeCode || ''}
                  onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'hookTypeCode', e.target.value)}
                  placeholder="内部编码"
                  className={inputClass}
                />
              </div>
              <div>
                <FieldLabel>反转编码</FieldLabel>
                <input
                  type="text"
                  value={ep.reversalCode || ''}
                  onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'reversalCode', e.target.value)}
                  placeholder="内部编码"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        </details>
        <div className="flex flex-wrap items-center gap-3">
          <label className="inline-flex items-center gap-2 text-sm text-navy-200">
            <input
              type="checkbox"
              checked={!!ep.isKeyEpisode}
              onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'isKeyEpisode', e.target.checked)}
              className="rounded border-navy-600"
            />
            关键集
          </label>
          <select
            value={ep.keyEpisodeType || ''}
            onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'keyEpisodeType', e.target.value)}
            className={`${inputClass} max-w-[180px]`}
          >
            {KEY_EPISODE_TYPES.map((opt) => (
              <option key={opt.value || 'none'} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <FieldLabel>备注</FieldLabel>
          <textarea
            value={ep.notes || ''}
            onChange={(e) => onUpdateEpisode(ep.episodeNumber, 'notes', e.target.value.slice(0, 500))}
            rows={3}
            maxLength={500}
            className={inputClass}
          />
        </div>
      </div>
    )
  }

  const stageName = ep.stageInfo?.stageName
  const chars = (ep.keyCharacters || []).join('、')
  const typeLabel = resolveKeyEpisodeTypeLabel(ep.keyEpisodeType)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {stageName && <MetaChip>{stageName}</MetaChip>}
        {ep.emotionalIntensity != null && <MetaChip>情绪 {ep.emotionalIntensity}/10</MetaChip>}
        {ep.sceneCount != null && <MetaChip>{ep.sceneCount} 场</MetaChip>}
        {ep.isKeyEpisode && <MetaChip>关键集</MetaChip>}
        {typeLabel && <MetaChip>{typeLabel}</MetaChip>}
        {resolveHookLabel(ep) ? (
          <MetaChip title={ep.hookTypeHint}>{resolveHookLabel(ep)}</MetaChip>
        ) : null}
        {resolveReversalLabel(ep) ? (
          <MetaChip title={ep.reversalPatternHint}>{resolveReversalLabel(ep)}</MetaChip>
        ) : null}
      </div>
      {ep.title && <p className="font-semibold text-white text-sm">{ep.title}</p>}
      <ReadonlyField label="本集梗概" value={ep.oneLineSummary} multiline />
      <ReadonlyField label="开头钩子" value={ep.hook} multiline />
      <ReadonlyField label="本集反转" value={ep.reversal} multiline />
      <ReadonlyField label="结尾悬念" value={ep.cliffhanger} multiline />
      <ReadonlyField label="主要角色" value={chars} />
      <ReadonlyField label="备注" value={ep.notes} multiline />
    </div>
  )
}

export function OutlineStagePanel({
  block,
  episodes,
  editMode,
  inputClass,
  activeEpNum,
  onSelectEpisode,
  onUpdateStageRough,
  onUpdateEpisode,
  onUpdateKeyCharacters,
  onGenerateStageRough,
  onGenerateNextEpisode,
  generating = false,
  skillBusy = false,
  coinCost = 0,
  currencyName = '币',
}) {
  if (!block) {
    return <p className="text-sm text-navy-400 text-center py-8">暂无阶段数据</p>
  }

  const { from, to } = blockRange(block)
  const blockEps = episodes.filter((e) => e.episodeNumber >= from && e.episodeNumber <= to)
  const activeEp =
    activeEpNum != null ? blockEps.find((e) => e.episodeNumber === activeEpNum) || null : null
  const stageRoughLen = (block.roughOutline || '').length
  const blockFilled = blockEps.filter((e) => e.filled).length
  const stageState = getStageGenerationState(block, episodes)
  const stageDirection = stageDirectionText(block)
  const disabled = generating || skillBusy

  return (
    <div className="space-y-5">
      {!editMode && (onGenerateStageRough || onGenerateNextEpisode) && (
        <div className="flex flex-wrap items-center gap-2 pb-1">
          {onGenerateStageRough && (
            <button
              type="button"
              disabled={disabled}
              onClick={() => onGenerateStageRough(block)}
              className="px-4 py-2 rounded-xl text-sm border border-gold-400/30 text-gold-200 hover:bg-gold-400/10 disabled:opacity-50 inline-flex items-center gap-2"
            >
              {disabled ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {stageState.roughReady ? '重新规划本阶段' : 'AI 规划本阶段'}
              {coinCost > 0 && (
                <span className="text-xs opacity-80">
                  {coinCost} {currencyName}
                </span>
              )}
            </button>
          )}
          {onGenerateNextEpisode && stageState.nextEp != null && (
            <button
              type="button"
              disabled={disabled || !stageState.roughReady}
              onClick={() => onGenerateNextEpisode(block)}
              className="px-4 py-2 rounded-xl text-sm btn-gold font-medium disabled:opacity-50 inline-flex items-center gap-2"
              title={!stageState.roughReady ? '请先 AI 规划本阶段方向' : undefined}
            >
              {disabled ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              生成第 {stageState.nextEp} 集集纲
              {coinCost > 0 && (
                <span className="text-xs opacity-80">
                  {coinCost} {currencyName}
                </span>
              )}
            </button>
          )}
          {stageState.pendingCount === 0 && stageState.roughReady && (
            <span className="text-xs text-navy-500">本阶段集纲已全部生成</span>
          )}
        </div>
      )}

      {!editMode && stageDirection && (
        <div className="rounded-xl border border-navy-700/30 bg-navy-900/35 px-4 py-3">
          <div className="text-[10px] text-navy-500 mb-1">阶段方向（策划摘要，非分集详情）</div>
          <p className="text-sm text-navy-200 leading-relaxed whitespace-pre-wrap">{stageDirection}</p>
          {looksLikeEpisodeDump(block.roughOutline) && (
            <p className="text-[11px] text-navy-500 mt-2">逐集内容请使用「生成第 N 集集纲」，不在此重复展示。</p>
          )}
        </div>
      )}

      {editMode && (
        <section>
          <div className="flex items-center justify-between gap-2 mb-2">
            <h5 className="text-sm font-medium text-white">
              阶段方向
              <span className="text-red-400 ml-1">*</span>
            </h5>
            <span className="text-[10px] text-navy-500">{stageRoughLen} / 500</span>
          </div>
          <textarea
            value={block.roughOutline || ''}
            onChange={(e) => onUpdateStageRough(block.key, e.target.value.slice(0, 500))}
            rows={4}
            maxLength={500}
            placeholder="本阶段整体方向：核心任务、情绪基调、阶段收束（勿写逐集梗概，分集请用下方集纲）"
            className={`${inputClass} min-h-[100px]`}
          />
        </section>
      )}

      <section>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-gold-400/80" />
            <h5 className="text-sm font-medium text-white">
              分集集纲
              {editMode && <span className="text-red-400 ml-1">*</span>}
            </h5>
          </div>
          <span className="text-[10px] text-navy-500">
            {blockFilled}/{blockEps.length} 集
          </span>
        </div>

        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1 mb-4">
          {blockEps.map((ep) => {
            const selected = (activeEp?.episodeNumber ?? null) === ep.episodeNumber
            return (
              <button
                key={ep.episodeNumber}
                type="button"
                onClick={() => onSelectEpisode(ep.episodeNumber)}
                className={`w-full text-left rounded-xl border px-4 py-3 transition-colors ${
                  selected
                    ? 'border-gold-400/40 bg-gold-400/10'
                    : ep.filled
                      ? 'border-navy-600/30 bg-navy-900/40 hover:bg-navy-800/50'
                      : 'border-dashed border-navy-600/40 bg-navy-950/30 hover:bg-navy-900/40'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm text-white font-medium">第{ep.episodeNumber}集</span>
                  <span className="text-[10px] text-navy-500">
                    {ep.filled ? ep.title || '已填充' : '待生成'}
                  </span>
                </div>
                {ep.filled && !selected && (
                  <p className="text-xs text-navy-400 mt-1 line-clamp-2">{episodePreview(ep)}</p>
                )}
              </button>
            )
          })}
        </div>

        {activeEp ? (
          <div className="pt-4 border-t border-navy-700/30">
            <OutlineEpisodeDetail
              ep={activeEp}
              editMode={editMode}
              inputClass={inputClass}
              onUpdateEpisode={onUpdateEpisode}
              onUpdateKeyCharacters={onUpdateKeyCharacters}
            />
          </div>
        ) : (
          !editMode &&
          blockEps.some((e) => e.filled) && (
            <div className="space-y-3 pt-2">
              {blockEps
                .filter((e) => e.filled)
                .map((ep) => (
                  <button
                    key={ep.episodeNumber}
                    type="button"
                    onClick={() => onSelectEpisode(ep.episodeNumber)}
                    className="w-full text-left"
                  >
                    <OutlineEpisodeCard ep={ep} />
                  </button>
                ))}
            </div>
          )
        )}
      </section>
    </div>
  )
}

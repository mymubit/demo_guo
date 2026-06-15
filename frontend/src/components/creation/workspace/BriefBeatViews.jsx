import { BookMarked, Clock, Film, FileText, Sparkles, TrendingUp, Users } from 'lucide-react'
import { StructureMetaStrip } from './StructureBeatViews'

const STORY_FIELDS = [
  { key: 'idea', label: '一句话梗概', rows: 3, hero: true },
  { key: 'coreConflict', label: '核心冲突', rows: 3 },
  { key: 'emotionalTone', label: '情绪基调', rows: 1 },
  { key: 'openingHooks', label: '前三集钩子', rows: 4, hooks: true },
]

function PanelBlock({ title, icon: Icon, children, className = '' }) {
  if (!children) return null
  return (
    <div className={`rounded-2xl border border-navy-700/30 bg-navy-950/30 overflow-hidden ${className}`}>
      {title ? (
        <div className="px-4 py-2.5 border-b border-navy-700/25 bg-navy-900/35 flex items-center gap-2">
          {Icon ? <Icon className="w-3.5 h-3.5 text-gold-400/70" /> : null}
          <span className="text-xs font-medium text-gold-400/85">{title}</span>
        </div>
      ) : null}
      <div className="p-4">{children}</div>
    </div>
  )
}

function parseOpeningHooks(text) {
  if (!text?.trim()) return []
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const epMatch = line.match(/^第?\s*(\d+)\s*集[：:]\s*(.+)$/)
      if (epMatch) return { episode: epMatch[1], text: epMatch[2] }
      const numMatch = line.match(/^(\d+)[\.、]\s*(.+)$/)
      if (numMatch) return { episode: numMatch[1], text: numMatch[2] }
      return { episode: String(index + 1), text: line }
    })
}

export function StoryBriefPanel({ storyBrief = {}, editMode, inputClass, onUpdateField }) {
  const sb = storyBrief
  const hooks = parseOpeningHooks(sb.openingHooks)

  if (editMode) {
    return (
      <div className="space-y-4">
        {STORY_FIELDS.map(({ key, label, rows }) => (
          <div key={key}>
            <div className="text-xs text-navy-500 mb-1.5">{label}</div>
            {rows === 1 ? (
              <input
                type="text"
                value={sb[key] || ''}
                onChange={(e) => onUpdateField?.(key, e.target.value)}
                className={inputClass}
              />
            ) : (
              <textarea
                value={sb[key] || ''}
                onChange={(e) => onUpdateField?.(key, e.target.value)}
                rows={rows}
                className={inputClass}
              />
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sb.idea ? (
        <div className="rounded-2xl border border-gold-400/15 bg-gradient-to-br from-gold-400/8 via-navy-950/20 to-transparent border-l-4 border-l-gold-400/45 px-4 py-4">
          <div className="text-xs font-medium text-gold-400/90 mb-2">一句话梗概</div>
          <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{sb.idea}</p>
        </div>
      ) : null}

      {(sb.coreConflict || sb.emotionalTone) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {sb.coreConflict ? (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
              <div className="text-[10px] text-amber-300/80 mb-1.5">核心冲突</div>
              <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">
                {sb.coreConflict}
              </p>
            </div>
          ) : null}
          {sb.emotionalTone ? (
            <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 px-4 py-3">
              <div className="text-[10px] text-violet-300/80 mb-1.5">情绪基调</div>
              <p className="text-sm text-white font-medium">{sb.emotionalTone}</p>
            </div>
          ) : null}
        </div>
      )}

      {hooks.length > 0 ? (
        <PanelBlock title="前三集钩子" icon={Sparkles}>
          <div className="space-y-0">
            {hooks.map((hook, index) => {
              const isLast = index === hooks.length - 1
              return (
                <div key={`hook-${hook.episode}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
                  {!isLast ? (
                    <span
                      className="absolute left-[15px] top-8 bottom-0 w-px bg-gradient-to-b from-gold-400/35 to-navy-700/15"
                      aria-hidden
                    />
                  ) : null}
                  <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-gold-400/45 bg-navy-900 text-xs font-bold text-gold-300">
                    E{hook.episode}
                  </div>
                  <p className="flex-1 text-sm text-navy-100 leading-relaxed pt-1">{hook.text}</p>
                </div>
              )
            })}
          </div>
        </PanelBlock>
      ) : null}
    </div>
  )
}

export function ProjectSpecPanel({
  theme,
  episodes,
  meta = {},
  editMode,
  inputClass,
  onUpdateField,
}) {
  const specItems = [
    meta.formatVariantDisplayName,
    meta.targetPlatform,
    meta.episodeDurationMinutes ? `${meta.episodeDurationMinutes} 分钟/集` : null,
    meta.budgetLevel ? `预算 ${meta.budgetLevel}` : null,
    meta.creationEntry,
  ].filter(Boolean)

  if (editMode) {
    return (
      <div className="space-y-4 rounded-2xl border border-navy-700/30 bg-navy-950/30 p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-navy-500 mb-1.5">题材</div>
            <input
              type="text"
              value={theme || ''}
              onChange={(e) => onUpdateField?.('themeDisplayName', e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <div className="text-xs text-navy-500 mb-1.5">集数</div>
            <input
              type="text"
              value={episodes || ''}
              onChange={(e) => onUpdateField?.('episodeCount', e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
        {specItems.length > 0 ? (
          <p className="text-[11px] text-navy-500">格式、平台等参数由立项时确定，此处仅可编辑题材与集数。</p>
        ) : null}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-xl border border-gold-400/20 bg-gold-400/5 px-4 py-4">
          <div className="flex items-center gap-2 text-[10px] text-gold-400/80 mb-2">
            <Film className="w-3.5 h-3.5" />
            题材类型
          </div>
          <div className="text-lg font-semibold text-white leading-snug">{theme || '—'}</div>
        </div>
        {episodes ? (
          <div className="rounded-xl border border-navy-700/30 bg-navy-900/40 px-4 py-4">
            <div className="flex items-center gap-2 text-[10px] text-navy-500 mb-2">
              <Clock className="w-3.5 h-3.5" />
              计划集数
            </div>
            <div className="text-lg font-semibold text-white">
              {episodes}
              <span className="text-sm font-normal text-navy-400 ml-1">集</span>
            </div>
          </div>
        ) : null}
      </div>

      {specItems.length > 0 ? (
        <PanelBlock title="制作规格" icon={FileText}>
          <div className="flex flex-wrap gap-2">
            {specItems.map((item) => (
              <span
                key={item}
                className="inline-flex text-xs px-2.5 py-1 rounded-lg bg-navy-800/60 border border-navy-600/25 text-navy-100"
              >
                {item}
              </span>
            ))}
          </div>
        </PanelBlock>
      ) : null}
    </div>
  )
}

export function TrendFormulaPanel({ trendFormula }) {
  const tf = trendFormula
  if (!tf) return null

  const highlights = (tf.highlights || []).filter(Boolean)

  return (
    <div className="space-y-4">
      <p className="text-[11px] text-navy-500">根据所选题材自动匹配，无需单独填写</p>

      {(tf.themeDisplayName || tf.theme) && (
        <div className="rounded-xl border border-navy-700/30 bg-navy-900/40 px-4 py-3">
          <div className="text-[10px] text-navy-500 mb-1">匹配题材</div>
          <div className="text-sm text-white">{tf.themeDisplayName || tf.theme}</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {tf.audienceFit ? (
          <div className="rounded-xl border border-cyan-500/15 bg-cyan-500/5 px-4 py-3">
            <div className="text-[10px] text-cyan-300/70 mb-1.5">受众画像</div>
            <p className="text-sm text-navy-100 leading-relaxed">{tf.audienceFit}</p>
          </div>
        ) : null}
        {tf.coreConflictFormula ? (
          <div className="rounded-xl border border-amber-500/15 bg-amber-500/5 px-4 py-3">
            <div className="text-[10px] text-amber-300/70 mb-1.5">冲突公式</div>
            <p className="text-sm text-navy-100 leading-relaxed">{tf.coreConflictFormula}</p>
          </div>
        ) : null}
      </div>

      {highlights.length > 0 ? (
        <PanelBlock title="题材亮点" icon={TrendingUp}>
          <div className="flex flex-wrap gap-2">
            {highlights.map((line, i) => (
              <span
                key={`tf-h-${i}`}
                className="inline-flex max-w-full text-[11px] leading-snug px-2.5 py-1.5 rounded-lg bg-navy-800/60 border border-gold-400/15 text-navy-100"
              >
                {line}
              </span>
            ))}
          </div>
        </PanelBlock>
      ) : null}

      {tf.structuralNotes ? (
        <p className="text-xs text-navy-400 leading-relaxed border-t border-navy-700/20 pt-3">
          {tf.structuralNotes}
        </p>
      ) : null}
    </div>
  )
}

export function SupplementPanel({
  audience,
  reference,
  notes,
  writingBrief,
  editMode,
  inputClass,
  onUpdateField,
}) {
  const hasWriting = writingBrief?.tone || writingBrief?.notes
  const hasContent = audience || reference || notes || hasWriting

  if (!hasContent && !editMode) return null

  return (
    <div className="space-y-4">
      {(audience || editMode) && (
        <PanelBlock title="目标受众" icon={Users}>
          {editMode ? (
            <textarea
              value={audience || ''}
              onChange={(e) => onUpdateField?.('targetAudience', e.target.value)}
              rows={3}
              className={inputClass}
            />
          ) : (
            <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{audience}</p>
          )}
        </PanelBlock>
      )}

      {hasWriting && !editMode ? (
        <PanelBlock title="写作指引" icon={FileText}>
          <p className="text-[11px] text-navy-500 mb-3">由故事策划自动整理</p>
          {writingBrief.tone ? (
            <div className="rounded-lg border border-navy-700/25 bg-navy-900/35 px-3 py-2 mb-3">
              <div className="text-[10px] text-navy-500 mb-1">基调</div>
              <p className="text-sm text-navy-100">{writingBrief.tone}</p>
            </div>
          ) : null}
          {writingBrief.notes ? (
            <p className="text-sm text-navy-300 leading-relaxed whitespace-pre-wrap">
              {writingBrief.notes}
            </p>
          ) : null}
        </PanelBlock>
      ) : null}

      {(reference || editMode) && (
        <PanelBlock title="参考作品" icon={BookMarked}>
          {editMode ? (
            <input
              type="text"
              value={reference || ''}
              onChange={(e) => onUpdateField?.('referenceWork', e.target.value)}
              className={inputClass}
            />
          ) : (
            <p className="text-sm text-navy-100">{reference}</p>
          )}
        </PanelBlock>
      )}

      {(notes || editMode) && (
        <PanelBlock title="备注" icon={FileText}>
          {editMode ? (
            <textarea
              value={notes || ''}
              onChange={(e) => onUpdateField?.('notes', e.target.value)}
              rows={2}
              className={inputClass}
            />
          ) : (
            <p className="text-sm text-navy-100 whitespace-pre-wrap">{notes}</p>
          )}
        </PanelBlock>
      )}
    </div>
  )
}

export function ThemeRecommendationsPanel({ recommendations = [] }) {
  const recs = (recommendations || []).filter(Boolean)
  if (!recs.length) return null
  return (
    <PanelBlock title="题材推荐" icon={Sparkles}>
      <ul className="space-y-2">
        {recs.slice(0, 5).map((rec) => (
          <li
            key={rec.themeCode || rec.displayName}
            className="rounded-lg border border-navy-700/25 bg-navy-900/35 px-3 py-2"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-white font-medium">{rec.displayName || rec.themeCode}</span>
              {rec.matched ? (
                <span className="text-[10px] text-green-400/90 border border-green-500/30 px-1.5 py-0.5 rounded">
                  当前题材
                </span>
              ) : null}
              {rec.trendTag ? (
                <span className="text-[10px] text-gold-400/80">{rec.trendTag}</span>
              ) : null}
            </div>
            {rec.audienceFit ? (
              <p className="text-xs text-navy-400 mt-1 line-clamp-2">{rec.audienceFit}</p>
            ) : null}
            {rec.sampleHook ? (
              <p className="text-xs text-navy-300 mt-1 line-clamp-2">示例：{rec.sampleHook}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </PanelBlock>
  )
}

export function BriefMetaStrip({ items = [] }) {
  return <StructureMetaStrip items={items} />
}

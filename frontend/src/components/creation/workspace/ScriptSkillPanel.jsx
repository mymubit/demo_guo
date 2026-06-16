import { useEffect, useMemo, useState } from 'react'
import MasterDetailLayout, {
  AllContentShell,
  ContentSection,
  MetaChip,
  PickerTile,
} from './MasterDetailLayout'
import GateLogSection, { GateLogBadge } from './GateLogSection'

export default function ScriptSkillPanel({
  draft,
  editMode,
  onDraftChange,
  saving,
  onSave,
  episodes = [],
  navigation = [],
}) {
  const eps = episodes.length ? episodes : draft.episodes || []
  const nav = navigation.length ? navigation : draft.navigation || []
  const [activeId, setActiveId] = useState(eps[0] ? `ep-${eps[0].episodeNumber}` : null)
  const [navFilter, setNavFilter] = useState(null)

  const filteredEps = useMemo(() => {
    if (!navFilter) return eps
    return eps.filter(
      (e) =>
        e.episodeNumber >= navFilter.from_episode && e.episodeNumber <= navFilter.to_episode
    )
  }, [eps, navFilter])

  useEffect(() => {
    if (!eps.length) return
    if (!activeId || !eps.some((e) => `ep-${e.episodeNumber}` === activeId)) {
      setActiveId(`ep-${(navFilter ? filteredEps[0] : eps[0])?.episodeNumber}`)
    }
  }, [eps, filteredEps, activeId, navFilter])

  const activeEp = useMemo(() => {
    if (!activeId) return null
    const epNum = Number(String(activeId).replace('ep-', ''))
    return eps.find((e) => e.episodeNumber === epNum) || null
  }, [activeId, eps])

  function updateEpisode(episodeNumber, key, value) {
    onDraftChange((prev) => ({
      ...prev,
      episodes: (prev.episodes || []).map((e) =>
        e.episodeNumber === episodeNumber ? { ...e, [key]: value } : e
      ),
    }))
  }

  const inputClass =
    'sf-control resize-y'

  function renderEpisodeContent(ep) {
    if (!ep) return null

    return editMode ? (
      <div className="space-y-3">
        <div>
          <div className="text-xs text-navy-400 mb-1.5">集标题</div>
          <input
            type="text"
            value={ep.title || ''}
            onChange={(e) => updateEpisode(ep.episodeNumber, 'title', e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <div className="text-xs text-navy-400 mb-1.5">剧本正文</div>
          <textarea
            value={ep.scriptMarkdown || ''}
            onChange={(e) => updateEpisode(ep.episodeNumber, 'scriptMarkdown', e.target.value)}
            rows={18}
            className={`${inputClass} font-mono min-h-[320px]`}
            placeholder="剧本正文（Markdown）"
          />
        </div>
      </div>
    ) : (
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {ep.sceneCount > 0 && <MetaChip>{ep.sceneCount} 场</MetaChip>}
          {ep.wordCount > 0 && <MetaChip>{ep.wordCount} 字</MetaChip>}
          <GateLogBadge passed={ep.gatePassed ?? ep.gateLog?.passed} label="本集" />
        </div>
        {ep.gateLog && !ep.gateLog.skipped && ep.gateLog.passed === false && (
          <GateLogSection gateLog={ep.gateLog} title="逐集质检" />
        )}
        {(ep.polishRevisionNotes || []).length > 0 && (
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 px-3 py-2 text-xs text-navy-200 space-y-1">
            <div className="text-purple-300/90 font-medium">润色备注</div>
            {ep.polishRevisionNotes.slice(-3).map((note, i) => (
              <p key={i} className="whitespace-pre-wrap leading-relaxed">
                {typeof note === 'string' ? note : note.advice || note.text}
              </p>
            ))}
          </div>
        )}
        <pre className="text-sm text-navy-100 whitespace-pre-wrap font-sans leading-relaxed">
          {ep.scriptMarkdown || '（暂无正文）'}
        </pre>
      </div>
    )
  }

  function renderDetail() {
    if (!activeEp) {
      return <p className="text-sm text-navy-400 text-center py-8">暂无剧本，请先生成</p>
    }
    return renderEpisodeContent(activeEp)
  }

  const detailTitle = activeEp
    ? `第 ${activeEp.episodeNumber} 集${activeEp.title ? ` · ${activeEp.title}` : ''}`
    : '剧本'

  const metaChips = (
    <>
      <MetaChip>共 {draft.totalEpisodes || eps.length || 0} 集</MetaChip>
      <MetaChip>已生成 {draft.generatedCount ?? eps.length ?? 0} 集</MetaChip>
      <GateLogBadge passed={draft.creatorQualityGuardLog?.passed} label="语言" />
    </>
  )

  if (!editMode && eps.length > 0) {
    return (
      <AllContentShell meta={metaChips}>
        <GateLogSection gateLog={draft.creatorQualityGuardLog} title="语言校验" />
        {eps.map((ep) => (
          <ContentSection
            key={ep.episodeNumber}
            id={`script-ep-${ep.episodeNumber}`}
            title={`第 ${ep.episodeNumber} 集`}
            subtitle={ep.title || undefined}
          >
            {renderEpisodeContent(ep)}
          </ContentSection>
        ))}
      </AllContentShell>
    )
  }

  return (
    <MasterDetailLayout
      meta={metaChips}
      detailTitle={detailTitle}
      detail={renderDetail()}
      pickerLabel="分集目录"
      picker={
        <div className="space-y-3">
          {nav.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setNavFilter(null)}
                className={`px-2 py-1 rounded-lg text-[10px] border ${
                  !navFilter
                    ? 'border-gold-400/40 bg-gold-400/10 text-gold-200'
                    : 'border-white/10 text-navy-400 hover:text-navy-200'
                }`}
              >
                全部
              </button>
              {nav.map((block) => (
                <button
                  key={`${block.label}-${block.from_episode}`}
                  type="button"
                  onClick={() => {
                    setNavFilter(block)
                    setActiveId(`ep-${block.from_episode}`)
                  }}
                  className={`px-2 py-1 rounded-lg text-[10px] border ${
                    navFilter?.from_episode === block.from_episode
                      ? 'border-gold-400/40 bg-gold-400/10 text-gold-200'
                      : 'border-white/10 text-navy-400 hover:text-navy-200'
                  }`}
                >
                  {block.label}
                </button>
              ))}
            </div>
          )}
          <div className="max-h-[60vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-3 gap-2">
              {filteredEps.map((ep) => (
                <PickerTile
                  key={ep.episodeNumber}
                  active={activeId === `ep-${ep.episodeNumber}`}
                  onClick={() => setActiveId(`ep-${ep.episodeNumber}`)}
                  subtitle={
                    ep.wordCount
                      ? `${ep.wordCount}字`
                      : ep.title
                        ? ep.title.slice(0, 5)
                        : undefined
                  }
                >
                  第{ep.episodeNumber}集
                </PickerTile>
              ))}
            </div>
          </div>
        </div>
      }
      editMode={editMode && draft.editable !== false}
      saving={saving}
      onSave={() => onSave?.(draft)}
      showSave={!!onSave}
    />
  )
}

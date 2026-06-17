import { useEffect, useMemo, useState } from 'react'
import StructureSectionLayout from './StructureSectionLayout'
import {
  blockRange,
  buildOutlineNavSections,
  getStageGenerationState,
  OutlineMetaStrip,
  OutlineOverviewPanel,
  OutlinePlanningPanel,
  OutlineStagePanel,
  OutlineSummaryBanner,
} from './OutlineBeatViews'

export default function OutlineSkillPanel({
  draft,
  editMode,
  onDraftChange,
  saving,
  onSave,
  onGenerate,
  generating = false,
  skillBusy = false,
  coinCost = 0,
  currencyName = '币',
}) {
  const stageBlocks = draft.stageBlocks || draft.navigation || []
  const eps = draft.episodes || []

  const sections = useMemo(() => buildOutlineNavSections(draft), [draft])

  const defaultId = sections[0]?.id || 'overview'
  const [activeId, setActiveId] = useState(defaultId)
  const [activeEpByStage, setActiveEpByStage] = useState({})

  useEffect(() => {
    if (!sections.some((s) => s.id === activeId && !s.isGroup)) {
      setActiveId(defaultId)
    }
  }, [sections, activeId, defaultId])

  const activeSection = sections.find((s) => s.id === activeId)
  const activeStageKey = activeSection?.stageKey
  const activeBlock = stageBlocks.find((b) => b.key === activeStageKey) || null

  const activeEpNum = activeStageKey ? activeEpByStage[activeStageKey] ?? null : null

  useEffect(() => {
    if (!activeStageKey || !editMode) return
    const { from } = blockRange(activeBlock)
    if (activeEpByStage[activeStageKey] == null) {
      setActiveEpByStage((prev) => ({ ...prev, [activeStageKey]: from }))
    }
  }, [activeStageKey, activeBlock, editMode, activeEpByStage])

  const inputClass =
    'sf-control resize-y'

  function updateStructureSummary(value) {
    onDraftChange((prev) => ({ ...prev, structureSummary: value }))
  }

  function updateStageRough(key, value) {
    onDraftChange((prev) => ({
      ...prev,
      stageBlocks: (prev.stageBlocks || []).map((b) =>
        b.key === key ? { ...b, roughOutline: value.slice(0, 500) } : b
      ),
    }))
  }

  function updateEpisode(episodeNumber, field, value) {
    onDraftChange((prev) => ({
      ...prev,
      episodes: (prev.episodes || []).map((e) =>
        e.episodeNumber === episodeNumber ? { ...e, [field]: value, filled: true } : e
      ),
    }))
  }

  function updateKeyCharacters(episodeNumber, text) {
    const chars = text
      .split(/[,、，]/)
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 5)
    updateEpisode(episodeNumber, 'keyCharacters', chars)
  }

  function selectStageEpisode(stageKey, epNum) {
    setActiveEpByStage((prev) => ({ ...prev, [stageKey]: epNum }))
  }

  function jumpToEpisode(epNum) {
    const block = stageBlocks.find((b) => {
      const { from, to } = blockRange(b)
      return epNum >= from && epNum <= to
    })
    if (!block) return
    setActiveId(`stage-${block.key}`)
    setActiveEpByStage((prev) => ({ ...prev, [block.key]: epNum }))
  }

  function handleGenerateStageRough(block) {
    if (!block?.key || !onGenerate) return
    onGenerate({
      outline_mode: 'stage_framework',
      stage_key: block.key,
    })
  }

  function handleGenerateNextEpisode(block) {
    if (!block || !onGenerate) return
    const stageState = getStageGenerationState(block, eps)
    const nextEp = stageState.nextEp
    if (nextEp == null) return
    onGenerate({
      outline_mode: 'block',
      from_episode: nextEp,
      to_episode: nextEp,
      batch_size: 1,
    })
  }

  function renderSectionContent(sectionId) {
    if (sectionId === 'overview') {
      return <OutlineOverviewPanel draft={draft} onJumpToEpisode={jumpToEpisode} />
    }

    if (sectionId === 'planning') {
      return <OutlinePlanningPanel draft={draft} />
    }

    if (sectionId.startsWith('stage-') && activeBlock) {
      return (
        <OutlineStagePanel
          block={activeBlock}
          episodes={eps}
          editMode={editMode}
          inputClass={inputClass}
          activeEpNum={activeEpNum}
          onSelectEpisode={(num) => selectStageEpisode(activeBlock.key, num)}
          onUpdateStageRough={updateStageRough}
          onUpdateEpisode={updateEpisode}
          onUpdateKeyCharacters={updateKeyCharacters}
          onGenerateStageRough={onGenerate ? handleGenerateStageRough : undefined}
          onGenerateNextEpisode={onGenerate ? handleGenerateNextEpisode : undefined}
          generating={generating}
          skillBusy={skillBusy}
          coinCost={coinCost}
          currencyName={currencyName}
        />
      )
    }

    return null
  }

  if (!sections.length) {
    return (
      <div className="space-y-4">
        <OutlineSummaryBanner
          summary={draft.structureSummary}
          editMode={editMode}
          onChange={updateStructureSummary}
          inputClass={inputClass}
        />
        <div className="rounded-2xl border border-white/5 bg-slate-900/40 px-6 py-12 text-center text-sm text-navy-400">
          暂无大纲内容，请使用 AI 生成
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <OutlineSummaryBanner
        summary={draft.structureSummary}
        editMode={editMode}
        onChange={updateStructureSummary}
        inputClass={inputClass}
      />
      <StructureSectionLayout
        meta={<OutlineMetaStrip draft={draft} />}
        sections={sections}
        activeId={activeId}
        onSelect={setActiveId}
        editMode={editMode && draft.editable !== false}
        saving={saving}
        onSave={() => onSave?.(draft)}
        showSave={!!onSave}
        navLabel="大纲模块"
        fallbackTitle="大纲"
      >
        {renderSectionContent(activeId)}
      </StructureSectionLayout>
    </div>
  )
}

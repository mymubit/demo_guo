import { useEffect, useMemo, useState } from 'react'
import { composeCoreIdea } from '@/utils/storyBrief'
import StructureSectionLayout from './StructureSectionLayout'
import {
  BriefMetaStrip,
  ProjectSpecPanel,
  StoryBriefPanel,
  SupplementPanel,
  TrendFormulaPanel,
  ThemeRecommendationsPanel,
} from './BriefBeatViews'

export default function BriefSkillPanel({ draft, editMode, onDraftChange, saving, onSave }) {
  const meta = draft.meta || {}
  const sb = draft.storyBrief || {}

  const inputClass =
    'sf-control resize-y'

  function fieldValue(key) {
    return (draft.fields || []).find((f) => f.key === key)?.value || ''
  }

  function updateField(key, value) {
    onDraftChange((prev) => ({
      ...prev,
      fields: (prev.fields || []).map((f) => (f.key === key ? { ...f, value } : f)),
    }))
  }

  function updateStory(key, value) {
    onDraftChange((prev) => ({
      ...prev,
      storyBrief: { ...(prev.storyBrief || {}), [key]: value },
    }))
  }

  const theme = fieldValue('themeDisplayName') || meta.themeDisplayName
  const episodes = fieldValue('episodeCount') || meta.episodeCount
  const audience = fieldValue('targetAudience')
  const reference = fieldValue('referenceWork')
  const notes = fieldValue('notes')

  const hasStoryBrief =
    sb.idea || sb.coreConflict || sb.emotionalTone || sb.openingHooks || editMode

  const hasTrend =
    draft.trendFormula &&
    (draft.trendFormula.audienceFit ||
      draft.trendFormula.coreConflictFormula ||
      (draft.trendFormula.highlights || []).length ||
      draft.trendFormula.structuralNotes ||
      draft.trendFormula.themeDisplayName ||
      draft.trendFormula.theme ||
      draft.trendFormula.projectHook ||
      draft.trendFormula.projectIdea ||
      draft.trendFormula.sampleHook)
  const hasThemeRecs = (draft.themeRecommendations || []).length > 0

  const hasSupplement =
    audience ||
    reference ||
    notes ||
    draft.writingBrief?.tone ||
    draft.writingBrief?.notes ||
    editMode

  const sections = useMemo(() => {
    const items = []
    if (hasStoryBrief) {
      items.push({ id: 'story', label: '故事策划', subtitle: '梗概与钩子' })
    }
    items.push({ id: 'spec', label: '项目规格', subtitle: theme || '题材·集数' })
    if (hasTrend) {
      items.push({ id: 'trend', label: '题材趋势', subtitle: '自动匹配' })
    }
    if (hasThemeRecs) {
      items.push({ id: 'theme-rec', label: '题材推荐', subtitle: '对标选题' })
    }
    if (hasSupplement) {
      items.push({ id: 'supplement', label: '补充参考', subtitle: '受众与备注' })
    }
    return items
  }, [hasStoryBrief, hasTrend, hasThemeRecs, hasSupplement, theme, sb, editMode])

  const [activeId, setActiveId] = useState('story')

  useEffect(() => {
    if (!sections.some((s) => s.id === activeId)) {
      setActiveId(sections[0]?.id || null)
    }
  }, [sections, activeId])

  function handleSave() {
    const merged = { ...(draft.storyBrief || {}) }
    const coreHook = composeCoreIdea({
      idea: merged.idea,
      coreConflict: merged.coreConflict,
      emotionalTone: merged.emotionalTone,
      openingHooks: merged.openingHooks,
    })
    onSave?.({
      ...draft,
      fields: (draft.fields || []).map((f) =>
        f.key === 'coreHook' ? { ...f, value: coreHook } : f
      ),
    })
  }

  function renderSectionContent(sectionId) {
    if (sectionId === 'story') {
      return (
        <StoryBriefPanel
          storyBrief={sb}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateField={updateStory}
        />
      )
    }

    if (sectionId === 'spec') {
      return (
        <ProjectSpecPanel
          theme={theme}
          episodes={episodes}
          meta={meta}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateField={updateField}
        />
      )
    }

    if (sectionId === 'trend') {
      return <TrendFormulaPanel trendFormula={draft.trendFormula} />
    }

    if (sectionId === 'theme-rec') {
      return <ThemeRecommendationsPanel recommendations={draft.themeRecommendations} />
    }

    if (sectionId === 'supplement') {
      return (
        <SupplementPanel
          audience={audience}
          reference={reference}
          notes={notes}
          writingBrief={draft.writingBrief}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateField={updateField}
        />
      )
    }

    return null
  }

  const metaItems = [
    theme,
    episodes ? `${episodes} 集` : null,
    meta.formatVariantDisplayName,
    meta.targetPlatform,
  ].filter(Boolean)

  if (!sections.length) {
    return <div className="py-12 text-center text-sm text-navy-400">暂无立项内容</div>
  }

  return (
    <StructureSectionLayout
      meta={<BriefMetaStrip items={metaItems} />}
      sections={sections}
      activeId={activeId}
      onSelect={setActiveId}
      editMode={editMode && draft.editable !== false}
      saving={saving}
      onSave={handleSave}
      showSave={!!onSave}
      navLabel="立项模块"
      fallbackTitle="立项策划"
    >
      {renderSectionContent(activeId)}
    </StructureSectionLayout>
  )
}

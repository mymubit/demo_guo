import { useEffect, useMemo, useState } from 'react'
import StructureSectionLayout from './StructureSectionLayout'
import RhythmCurveChart from './RhythmCurveChart'
import {
  RhythmBeatList,
  ReversalTimeline,
  StoryStructurePanel,
  StructureMetaStrip,
  WorldviewPanel,
  hasWorldviewContent,
} from './StructureBeatViews'
import { buildStructureSankeyOption } from '@/components/charts'

export default function StructureSkillPanel({ draft, editMode, onDraftChange, saving, onSave }) {
  const plan = draft.structurePlan || {}
  const wv = plan.worldview || {}
  const arc = plan.coreStoryArc || {}
  const constraints = plan.structuralConstraints || {}

  const inputClass =
    'w-full rounded-xl bg-navy-950/50 border border-navy-600/30 text-white text-sm px-4 py-3 focus:border-gold-400/50 outline-none resize-y'

  const hasWorldviewContentData = hasWorldviewContent(wv)
  const validationLog = plan.worldValidationLog
  const hasWorldviewValidation = Boolean(
    validationLog &&
      !validationLog.skipped &&
      (validationLog.passed || (validationLog.issues || []).length)
  )

  const hasWorldview = hasWorldviewContentData || hasWorldviewValidation || editMode

  const hasStructure =
    Object.values(arc).some(Boolean) ||
    (plan.sixStagePlan || []).length > 0 ||
    editMode

  const sections = useMemo(() => {
    const items = []
    if (hasWorldview) {
      items.push({ id: 'worldview', label: '世界观', subtitle: '设定' })
    }
    if (hasStructure) {
      const stageCount = (plan.sixStagePlan || []).length
      items.push({
        id: 'structure',
        label: '故事结构',
        subtitle: stageCount ? `${stageCount} 阶段` : '故事弧',
      })
    }
    if ((plan.rhythmCurve || []).length) {
      items.push({ id: 'rhythm', label: '节奏曲线', subtitle: `${plan.rhythmCurve.length} 段` })
    }
    if ((plan.keyReversalPoints || []).length) {
      items.push({
        id: 'reversals',
        label: '反转点',
        subtitle: `${plan.keyReversalPoints.length} 个`,
      })
    }
    return items
  }, [hasWorldview, hasStructure, plan, arc, editMode])

  const [activeId, setActiveId] = useState('worldview')

  const structureSankey = useMemo(() => {
    const raw = buildStructureSankeyOption({ structurePlan: plan })
    if (!raw) return { option: null, height: 320 }
    const { _chartHeight, ...option } = raw
    return { option, height: _chartHeight || 320 }
  }, [plan])

  useEffect(() => {
    if (!sections.some((s) => s.id === activeId)) {
      setActiveId(sections[0]?.id || null)
    }
  }, [sections, activeId])

  function updateWorldview(key, value) {
    onDraftChange((prev) => ({
      ...prev,
      structurePlan: {
        ...(prev.structurePlan || {}),
        worldview: { ...(prev.structurePlan?.worldview || {}), [key]: value },
      },
    }))
  }

  function updateArc(key, value) {
    onDraftChange((prev) => ({
      ...prev,
      structurePlan: {
        ...(prev.structurePlan || {}),
        coreStoryArc: { ...(prev.structurePlan?.coreStoryArc || {}), [key]: value },
      },
    }))
  }

  function updateRootRules(text) {
    const rules = text
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    updateWorldview('rootRules', rules)
  }

  function updateStage(stageIndex, field, value) {
    onDraftChange((prev) => ({
      ...prev,
      structurePlan: {
        ...(prev.structurePlan || {}),
        sixStagePlan: (prev.structurePlan?.sixStagePlan || []).map((s) =>
          s.stageIndex === stageIndex ? { ...s, [field]: value } : s
        ),
      },
    }))
  }

  function updateRhythmBlock(episodeRange, field, value) {
    onDraftChange((prev) => ({
      ...prev,
      structurePlan: {
        ...(prev.structurePlan || {}),
        rhythmCurve: (prev.structurePlan?.rhythmCurve || []).map((b) =>
          b.episodeRange === episodeRange ? { ...b, [field]: value } : b
        ),
      },
    }))
  }

  function updateRhythmEvents(episodeRange, text) {
    const events = text
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    updateRhythmBlock(episodeRange, 'keyEvents', events)
  }

  function updateReversal(episodeNumber, field, value) {
    onDraftChange((prev) => ({
      ...prev,
      structurePlan: {
        ...(prev.structurePlan || {}),
        keyReversalPoints: (prev.structurePlan?.keyReversalPoints || []).map((r) =>
          r.episodeNumber === episodeNumber ? { ...r, [field]: value } : r
        ),
      },
    }))
  }

  function renderSectionContent(sectionId) {
    if (sectionId === 'structure') {
      return (
        <StoryStructurePanel
          arc={arc}
          stages={plan.sixStagePlan || []}
          actStructure={plan.actStructure || {}}
          sankeyOption={structureSankey.option}
          sankeyHeight={structureSankey.height}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateArc={updateArc}
          onUpdateStage={updateStage}
        />
      )
    }

    if (sectionId === 'rhythm') {
      return (
        <div className="space-y-4">
          <RhythmCurveChart curve={plan.rhythmCurve} showSummaryGrid={false} />
          <RhythmBeatList
            blocks={plan.rhythmCurve}
            editMode={editMode}
            inputClass={inputClass}
            onUpdateBlock={updateRhythmBlock}
            onUpdateEvents={updateRhythmEvents}
          />
        </div>
      )
    }

    if (sectionId === 'reversals') {
      return (
        <ReversalTimeline
          points={plan.keyReversalPoints}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateReversal={updateReversal}
        />
      )
    }

    if (sectionId === 'worldview') {
      const validationLog = plan.worldValidationLog
      const validationIssues =
        validationLog && !validationLog.passed && !validationLog.skipped
          ? (validationLog.issues || []).filter(Boolean)
          : []

      return (
        <WorldviewPanel
          worldview={wv}
          validationLog={validationLog}
          validationIssues={validationIssues}
          editMode={editMode}
          inputClass={inputClass}
          onUpdateField={updateWorldview}
          onUpdateRootRules={updateRootRules}
        />
      )
    }

    return null
  }

  function renderConstraintMeta() {
    const items = []
    if (plan.workingTitle) items.push(plan.workingTitle)
    if (plan.totalEpisodes) items.push(`${plan.totalEpisodes} 集`)
    if (plan.formatVariantLabel) items.push(plan.formatVariantLabel)
    if (constraints.maxScenesPerEpisode != null) {
      items.push(`每集最多 ${constraints.maxScenesPerEpisode} 场`)
    }
    if (constraints.hookThresholdSeconds != null) {
      items.push(`${constraints.hookThresholdSeconds}s 内出钩子`)
    }
    if (constraints.minReversalsPerEpisode != null) {
      items.push(`每集至少 ${constraints.minReversalsPerEpisode} 反转`)
    }
    if (constraints.targetConflictDensity != null) {
      items.push(`冲突密度 ${constraints.targetConflictDensity}`)
    }
    if (constraints.keyEpisodeEveryNEpisodes != null) {
      items.push(`每 ${constraints.keyEpisodeEveryNEpisodes} 集大高潮`)
    }
    if (constraints.emotionalCurveMonotonicRising != null) {
      items.push(constraints.emotionalCurveMonotonicRising ? '情绪整体上升' : '情绪非单调')
    }
    return <StructureMetaStrip items={items} />
  }

  const metaChips = renderConstraintMeta()

  if (!sections.length) {
    return <div className="py-12 text-center text-sm text-navy-400">暂无结构内容</div>
  }

  return (
    <StructureSectionLayout
      meta={metaChips}
      sections={sections}
      activeId={activeId}
      onSelect={setActiveId}
      editMode={editMode && draft.editable !== false}
      saving={saving}
      onSave={() => onSave?.({ ...draft, structurePlan: draft.structurePlan })}
      showSave={!!onSave}
      navLabel="结构模块"
      fallbackTitle="结构与世界观"
    >
      {renderSectionContent(activeId)}
    </StructureSectionLayout>
  )
}

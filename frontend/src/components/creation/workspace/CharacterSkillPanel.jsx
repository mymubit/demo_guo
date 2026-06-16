import { useEffect, useMemo, useState } from 'react'
import StructureSectionLayout from './StructureSectionLayout'
import GateLogSection from './GateLogSection'
import {
  buildCharacterNavSections,
  CharacterArchetypePanel,
  CharacterCreativeDnaPanel,
  CharacterMetaStrip,
  CharacterOverviewPanel,
  CharacterProfilePanel,
  CharacterRelationsPanel,
  CharacterSummaryBanner,
} from './CharacterBeatViews'

export default function CharacterSkillPanel({ draft, editMode, onDraftChange, saving, onSave }) {
  const bible = draft.characterBible || {}
  const characters = bible.characters || []

  const sections = useMemo(() => buildCharacterNavSections(bible), [bible])

  const defaultId = useMemo(() => {
    const firstChar = sections.find((s) => s.charId)
    return firstChar?.id || sections[0]?.id || null
  }, [sections])

  const [activeId, setActiveId] = useState(defaultId)

  useEffect(() => {
    if (!sections.some((s) => s.id === activeId && !s.isGroup)) {
      setActiveId(defaultId)
    }
  }, [sections, activeId, defaultId])

  const activeSection = sections.find((s) => s.id === activeId)
  const activeChar = characters.find(
    (c) => `char-${c.id || c.name}` === activeId || (activeSection?.charId && (c.id || c.name) === activeSection.charId)
  )

  const inputClass =
    'sf-control resize-y'

  function updateChar(id, field, value) {
    onDraftChange((prev) => ({
      ...prev,
      characterBible: {
        ...(prev.characterBible || {}),
        characters: (prev.characterBible?.characters || []).map((c) =>
          c.id === id ? { ...c, [field]: value } : c
        ),
      },
    }))
  }

  function updateSummary(value) {
    onDraftChange((prev) => ({
      ...prev,
      characterBible: { ...(prev.characterBible || {}), summary: value },
    }))
  }

  function renderSectionContent(sectionId) {
    if (sectionId === 'relations') {
      return <CharacterRelationsPanel bible={bible} onSelectCharacter={setActiveId} />
    }

    if (activeChar) {
      return (
        <CharacterProfilePanel
          key={activeChar.id || activeChar.name}
          char={activeChar}
          bible={bible}
          editMode={editMode}
          onChange={(field, value) => updateChar(activeChar.id, field, value)}
        />
      )
    }

    return (
      <CharacterOverviewPanel bible={bible} onSelectCharacter={setActiveId} />
    )
  }

  if (!sections.length) {
    return (
      <div className="space-y-4">
        <GateLogSection gateLog={draft.characterGateLog} title="人设校验" />
        <CharacterSummaryBanner
          summary={bible.summary}
          editMode={editMode}
          onChange={updateSummary}
          inputClass={inputClass}
        />
        <div className="rounded-2xl border border-white/5 bg-slate-900/40 px-6 py-12 text-center text-sm text-navy-400">
          暂无角色内容，请使用 AI 生成
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <GateLogSection gateLog={draft.characterGateLog} title="人设校验" />
      <CharacterSummaryBanner
        summary={bible.summary}
        editMode={editMode}
        onChange={updateSummary}
        inputClass={inputClass}
      />
      <CharacterArchetypePanel bible={bible} />
      <CharacterCreativeDnaPanel bible={bible} />
      <StructureSectionLayout
        meta={<CharacterMetaStrip bible={bible} />}
        sections={sections}
        activeId={activeId}
        onSelect={setActiveId}
        editMode={editMode && draft.editable !== false}
        saving={saving}
        onSave={() => onSave?.({ ...draft, characterBible: draft.characterBible })}
        showSave={!!onSave}
        navLabel="角色目录"
        fallbackTitle="角色设计"
      >
        {renderSectionContent(activeId)}
      </StructureSectionLayout>
    </div>
  )
}

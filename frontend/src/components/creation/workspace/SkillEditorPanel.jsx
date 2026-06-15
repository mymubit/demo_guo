import { useEffect, useState } from 'react'
import { Save, UserPlus } from 'lucide-react'
import { parseInspirationPlan } from '@/utils/storyBrief'
import { resolveRoleTypeLabel } from '@/utils/displayLabels'
import BriefSkillPanel from './BriefSkillPanel'
import CharacterSkillPanel from './CharacterSkillPanel'
import OutlineSkillPanel from './OutlineSkillPanel'
import ScriptSkillPanel from './ScriptSkillPanel'
import StructureSkillPanel from './StructureSkillPanel'

const ROLE_TYPE_OPTIONS = [
  { value: 'protagonist-female', label: '女主' },
  { value: 'protagonist-male', label: '男主' },
  { value: 'antagonist-female', label: '女反派' },
  { value: 'antagonist-male', label: '男反派' },
  { value: 'antagonist', label: '反派' },
  { value: 'supporting', label: '配角' },
  { value: 'cameo', label: '客串' },
]

function FieldInput({ field, onChange }) {
  const common =
    'w-full rounded-xl bg-navy-950/60 border border-navy-600/30 text-white text-sm px-4 py-3 focus:border-gold-400/50 outline-none'
  if (field.type === 'textarea') {
    return (
      <textarea
        value={field.value || ''}
        onChange={(e) => onChange(field.key, e.target.value)}
        rows={field.key === 'coreHook' || field.key === 'worldviewSummary' ? 5 : 3}
        className={`${common} resize-y min-h-[80px]`}
      />
    )
  }
  return (
    <input
      type="text"
      value={field.value || ''}
      onChange={(e) => onChange(field.key, e.target.value)}
      className={common}
    />
  )
}

export default function SkillEditorPanel({
  skill,
  editor,
  editMode,
  onSave,
  saving,
  onOutlineGenerate,
  outlineGenerating = false,
  skillBusy = false,
  coinCost = 0,
  currencyName = '币',
}) {
  const [draft, setDraft] = useState(null)

  useEffect(() => {
    if (!editor) return
    const copy = JSON.parse(JSON.stringify(editor))
    if (copy.mode === 'brief' && !copy.storyBrief) {
      const core = (copy.fields || []).find((f) => f.key === 'coreHook')?.value || ''
      copy.storyBrief = parseInspirationPlan(core)
    }
    setDraft(copy)
  }, [editor, skill?.index])

  if (!draft) {
    return (
      <div className="p-12 text-center text-navy-400 text-sm">
        暂无内容，请使用 AI 生成
      </div>
    )
  }

  function updateField(key, value) {
    setDraft((prev) => ({
      ...prev,
      fields: (prev.fields || []).map((f) => (f.key === key ? { ...f, value } : f)),
    }))
  }

  function updateCharacter(idx, key, value) {
    setDraft((prev) => ({
      ...prev,
      characters: (prev.characters || []).map((c, i) =>
        i === idx ? { ...c, [key]: value } : c
      ),
    }))
  }

  function addCharacter() {
    setDraft((prev) => ({
      ...prev,
      characters: [
        ...(prev.characters || []),
        {
          id: `new-${Date.now()}`,
          name: '',
          roleType: 'supporting',
          oneLineSummary: '',
          personality: '',
          background: '',
        },
      ],
    }))
  }

  function handleSave() {
    onSave?.(draft)
  }

  return (
    <div className="min-w-0">
      {draft.mode === 'brief' && (
        <BriefSkillPanel
          draft={draft}
          editMode={editMode}
          onDraftChange={setDraft}
          saving={saving}
          onSave={handleSave}
        />
      )}

      {draft.mode === 'structure' && draft.structurePlan && (
        <StructureSkillPanel
          draft={draft}
          editMode={editMode}
          onDraftChange={setDraft}
          saving={saving}
          onSave={handleSave}
        />
      )}

      {draft.mode === 'structure' &&
        !draft.structurePlan &&
        (draft.fields || []).map((field) => (
          <div key={field.key} className="mb-4">
            <label className="block text-xs text-navy-400 mb-1.5">{field.label}</label>
            {editMode ? (
              <FieldInput field={field} onChange={updateField} />
            ) : (
              <p className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed px-1">
                {field.value || '—'}
              </p>
            )}
          </div>
        ))}

      {draft.mode === 'characters' && draft.characterBible && (
        <CharacterSkillPanel
          draft={draft}
          editMode={editMode}
          onDraftChange={setDraft}
          saving={saving}
          onSave={handleSave}
        />
      )}

      {draft.mode === 'characters' && !draft.characterBible && (
        <>
          <div className="mb-4">
            <label className="block text-xs text-navy-400 mb-1.5">人物关系</label>
            {editMode ? (
              <textarea
                value={draft.relationshipSummary || ''}
                onChange={(e) =>
                  setDraft((p) => ({ ...p, relationshipSummary: e.target.value }))
                }
                rows={3}
                className="w-full rounded-xl bg-navy-950/60 border border-navy-600/30 text-white text-sm px-4 py-3 resize-y"
              />
            ) : (
              <p className="text-sm text-navy-100 whitespace-pre-wrap">
                {draft.relationshipSummary || '—'}
              </p>
            )}
          </div>
          {(draft.characters || []).map((c, idx) => (
            <div
              key={c.id || idx}
              className="rounded-xl border border-navy-700/40 bg-navy-950/40 p-4 space-y-3 mb-4"
            >
              <div className="flex flex-wrap gap-3">
                <div className="flex-1 min-w-[120px]">
                  <label className="text-xs text-navy-500">姓名</label>
                  {editMode ? (
                    <input
                      value={c.name || ''}
                      onChange={(e) => updateCharacter(idx, 'name', e.target.value)}
                      className="w-full mt-1 rounded-lg bg-navy-900/60 border border-navy-600/30 px-3 py-2 text-sm text-white"
                    />
                  ) : (
                    <p className="text-white font-semibold mt-1">{c.name || '—'}</p>
                  )}
                </div>
                <div className="w-28">
                  <label className="text-xs text-navy-500">定位</label>
                  {editMode ? (
                    <select
                      value={c.roleType || 'supporting'}
                      onChange={(e) => updateCharacter(idx, 'roleType', e.target.value)}
                      className="w-full mt-1 rounded-lg bg-navy-900/60 border border-navy-600/30 px-3 py-2 text-sm text-white"
                    >
                      {ROLE_TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-navy-200 mt-1 text-sm">{resolveRoleTypeLabel(c) || '—'}</p>
                  )}
                </div>
              </div>
              {['oneLineSummary', 'personality', 'background'].map((key) => (
                <div key={key}>
                  <label className="text-xs text-navy-500">
                    {key === 'oneLineSummary' ? '一句话' : key === 'personality' ? '性格' : '背景'}
                  </label>
                  {editMode ? (
                    <textarea
                      value={c[key] || ''}
                      onChange={(e) => updateCharacter(idx, key, e.target.value)}
                      rows={key === 'background' ? 4 : 2}
                      className="w-full mt-1 rounded-lg bg-navy-900/60 border border-navy-600/30 px-3 py-2 text-sm text-white resize-y"
                    />
                  ) : (
                    <p className="text-sm text-navy-100 mt-1 whitespace-pre-wrap">{c[key] || '—'}</p>
                  )}
                </div>
              ))}
            </div>
          ))}
          {editMode && (
            <button
              type="button"
              onClick={addCharacter}
              className="inline-flex items-center gap-2 text-sm text-gold-400 hover:text-gold-300"
            >
              <UserPlus className="w-4 h-4" />
              添加角色
            </button>
          )}
          {editMode && draft.editable !== false && (
            <div className="pt-2">
              <button
                type="button"
                disabled={saving}
                onClick={handleSave}
                className="px-5 py-2.5 rounded-xl bg-navy-700/60 hover:bg-navy-600/60 border border-navy-500/30 text-white text-sm inline-flex items-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? '保存中…' : '保存修改'}
              </button>
            </div>
          )}
        </>
      )}

      {draft.mode === 'outline' && (
        <OutlineSkillPanel
          draft={draft}
          editMode={editMode}
          onDraftChange={setDraft}
          saving={saving}
          onSave={handleSave}
          onGenerate={onOutlineGenerate}
          generating={outlineGenerating}
          skillBusy={skillBusy}
          coinCost={coinCost}
          currencyName={currencyName}
        />
      )}

      {draft.mode === 'scripts' && (
        <ScriptSkillPanel
          draft={draft}
          editMode={editMode}
          onDraftChange={setDraft}
          saving={saving}
          onSave={handleSave}
        />
      )}
    </div>
  )
}

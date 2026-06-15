import { useMemo } from 'react'

const inputCls =
  'w-full px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:border-gold-500/50 outline-none'
const labelCls = 'text-xs text-navy-400 mb-1 block'

export function csvToList(text) {
  return String(text || '')
    .split(/[,，\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export function listToCsv(list) {
  return (list || []).join(', ')
}

const SUB_SKILL_TYPES = ['rule', 'cli', 'retrieval', 'llm', 'llm+rule', 'retrieval+rule', 'trace']

function emptySubSkill() {
  return { id: '', type: 'rule', description: '' }
}

export function Tier1SectionPicker({ catalog = [], selected = [], onChange }) {
  const selectedSet = useMemo(() => new Set(selected || []), [selected])
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {catalog.map((section) => {
          const key = section.key || section
          const label = section.label || key
          const active = selectedSet.has(key)
          return (
            <button
              key={key}
              type="button"
              title={key}
              onClick={() => {
                const next = active
                  ? selected.filter((item) => item !== key)
                  : [...selected, key]
                onChange(next)
              }}
              className={`px-2 py-1 rounded-lg text-[11px] border transition-colors ${
                active
                  ? 'bg-gold-400/15 text-gold-300 border-gold-400/40'
                  : 'bg-navy-900/50 text-navy-400 border-navy-700/40 hover:border-navy-600'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>
      {!catalog.length ? (
        <p className="text-xs text-navy-500">暂无 Tier1 目录</p>
      ) : null}
      <label className="block">
        <span className={labelCls}>手动编辑（逗号分隔）</span>
        <input
          value={listToCsv(selected)}
          onChange={(e) => onChange(csvToList(e.target.value))}
          className={`${inputCls} font-mono text-xs`}
        />
      </label>
    </div>
  )
}

export function SubSkillEditor({ skills = [], onChange }) {
  function patchSkill(index, field, value) {
    const next = skills.map((item, idx) => (idx === index ? { ...item, [field]: value } : item))
    onChange(next)
  }

  function removeSkill(index) {
    onChange(skills.filter((_, idx) => idx !== index))
  }

  function addSkill() {
    onChange([...(skills || []), emptySubSkill()])
  }

  function moveSkill(index, delta) {
    const target = index + delta
    if (target < 0 || target >= skills.length) return
    const next = [...skills]
    ;[next[index], next[target]] = [next[target], next[index]]
    onChange(next)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-navy-400">子技能 ({skills.length})</span>
        <button type="button" onClick={addSkill} className="text-xs text-gold-400 hover:text-gold-300">
          + 添加
        </button>
      </div>
      {skills.map((skill, index) => (
        <div
          key={`${skill.id || 'skill'}-${index}`}
          className="p-3 rounded-xl border border-navy-700/40 bg-navy-950/40 space-y-2"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] text-navy-500 font-mono">#{index + 1}</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={index === 0}
                onClick={() => moveSkill(index, -1)}
                className="text-[10px] text-navy-400 hover:text-navy-200 disabled:opacity-30"
              >
                上移
              </button>
              <button
                type="button"
                disabled={index >= skills.length - 1}
                onClick={() => moveSkill(index, 1)}
                className="text-[10px] text-navy-400 hover:text-navy-200 disabled:opacity-30"
              >
                下移
              </button>
              <button
                type="button"
                onClick={() => removeSkill(index)}
                className="text-[10px] text-red-400/80 hover:text-red-300"
              >
                删除
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <label className="block">
              <span className={labelCls}>id</span>
              <input
                value={skill.id || ''}
                onChange={(e) => patchSkill(index, 'id', e.target.value)}
                className={`${inputCls} font-mono text-xs`}
              />
            </label>
            <label className="block">
              <span className={labelCls}>type</span>
              <select
                value={skill.type || 'rule'}
                onChange={(e) => patchSkill(index, 'type', e.target.value)}
                className={`${inputCls} text-xs`}
              >
                {SUB_SKILL_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block">
            <span className={labelCls}>description</span>
            <input
              value={skill.description || ''}
              onChange={(e) => patchSkill(index, 'description', e.target.value)}
              className={`${inputCls} text-xs`}
            />
          </label>
        </div>
      ))}
    </div>
  )
}

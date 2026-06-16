import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react'
import { cn } from '@/utils/cn'

const inputCls =
  'sf-control focus:border-gold-500/50 outline-none'
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

const TYPE_BADGE = {
  llm: 'bg-purple-500/15 text-purple-200 border-purple-400/30',
  cli: 'bg-cyan-500/15 text-cyan-200 border-cyan-400/30',
  rule: 'border-white/10 bg-white/[0.05] text-navy-200',
  retrieval: 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30',
  trace: 'bg-amber-500/15 text-amber-200 border-amber-400/30',
  'llm+rule': 'bg-violet-500/15 text-violet-200 border-violet-400/30',
  'retrieval+rule': 'bg-teal-500/15 text-teal-200 border-teal-400/30',
}

function emptySubSkill() {
  return { id: '', type: 'rule', description: '' }
}

function typeBadgeClass(type) {
  return TYPE_BADGE[type] || TYPE_BADGE.rule
}

function skillTitle(skill) {
  const id = String(skill?.id || '').trim()
  if (id) return id
  return '未命名技能'
}

/** 子技能卡片网格 — 只读展示或点击进入编辑 */
export function SubSkillCardGrid({
  skills = [],
  readonly = false,
  selectedIndex = null,
  onSelect,
}) {
  if (!skills.length) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-navy-400">
        暂无子技能
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
      {skills.map((skill, index) => {
        const active = selectedIndex === index
        const Tag = readonly ? 'div' : 'button'
        return (
          <Tag
            key={`${skill.id || 'skill'}-${index}`}
            type={readonly ? undefined : 'button'}
            onClick={readonly ? undefined : () => onSelect?.(active ? null : index)}
            className={cn(
              'rounded-xl border p-3 text-left transition-all min-h-[96px] flex flex-col',
              readonly
                ? 'border-white/10 bg-slate-900/40 cursor-default'
                : 'border-white/10 bg-slate-900/40 hover:border-purple-500/35 hover:bg-white/[0.05] cursor-pointer',
              active && !readonly && 'border-purple-400/45 ring-1 ring-purple-400/25 bg-purple-500/5',
            )}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <span className="text-xs font-mono font-medium text-white truncate">{skillTitle(skill)}</span>
              <span
                className={cn(
                  'shrink-0 px-1.5 py-0.5 rounded text-[10px] border',
                  typeBadgeClass(skill.type),
                )}
              >
                {skill.type || 'rule'}
              </span>
            </div>
            <p className="text-[11px] text-navy-300 leading-relaxed line-clamp-3 flex-1">
              {skill.description || '（无描述）'}
            </p>
            {skill.cli ? (
              <p className="text-[10px] font-mono text-cyan-400/80 mt-2 truncate">cli: {skill.cli}</p>
            ) : null}
            {!readonly ? (
              <span className="text-[10px] text-navy-500 mt-2">#{index + 1} · 点击编辑</span>
            ) : (
              <span className="text-[10px] text-navy-500 mt-2">#{index + 1}</span>
            )}
          </Tag>
        )
      })}
    </div>
  )
}

function SubSkillDetailForm({ skill, onPatch, onRemove, onMoveUp, onMoveDown, canMoveUp, canMoveDown }) {
  return (
    <div className="rounded-xl border border-purple-500/25 bg-slate-900/40 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-white">编辑技能</span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={!canMoveUp}
            onClick={onMoveUp}
            className="p-1.5 rounded-lg text-navy-400 hover:text-white disabled:opacity-30"
            title="上移"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
          <button
            type="button"
            disabled={!canMoveDown}
            onClick={onMoveDown}
            className="p-1.5 rounded-lg text-navy-400 hover:text-white disabled:opacity-30"
            title="下移"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onRemove}
            className="p-1.5 rounded-lg text-red-400/80 hover:text-red-300"
            title="删除"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className={labelCls}>技能 ID</span>
          <input
            value={skill.id || ''}
            onChange={(e) => onPatch('id', e.target.value)}
            className={`${inputCls} font-mono text-xs`}
          />
        </label>
        <label className="block">
          <span className={labelCls}>类型</span>
          <select
            value={skill.type || 'rule'}
            onChange={(e) => onPatch('type', e.target.value)}
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
        <span className={labelCls}>描述</span>
        <textarea
          rows={2}
          value={skill.description || ''}
          onChange={(e) => onPatch('description', e.target.value)}
          className={`${inputCls} text-xs resize-y`}
        />
      </label>
      {['cli', 'llm', 'llm+rule', 'retrieval+rule'].includes(skill.type) ? (
        <label className="block">
          <span className={labelCls}>CLI（可选）</span>
          <input
            value={skill.cli || ''}
            onChange={(e) => onPatch('cli', e.target.value)}
            className={`${inputCls} font-mono text-xs`}
            placeholder="sub-brief"
          />
        </label>
      ) : null}
      {String(skill.type || '').includes('llm') ? (
        <label className="block">
          <span className={labelCls}>handbook</span>
          <input
            value={skill.handbook || ''}
            onChange={(e) => onPatch('handbook', e.target.value)}
            className={`${inputCls} font-mono text-xs`}
            placeholder="nodes/node-4-outline.md"
          />
        </label>
      ) : null}
      {String(skill.type || '').includes('retrieval') ? (
        <label className="block">
          <span className={labelCls}>references（逗号分隔）</span>
          <input
            value={listToCsv(skill.references)}
            onChange={(e) => onPatch('references', csvToList(e.target.value))}
            className={`${inputCls} font-mono text-xs`}
          />
        </label>
      ) : null}
    </div>
  )
}

/** Agent 注册表：卡片选技能 + 下方编辑表单 */
export function SubSkillEditor({ skills = [], onChange }) {
  const [selectedIndex, setSelectedIndex] = useState(null)

  function patchSkill(index, field, value) {
    const next = skills.map((item, idx) => (idx === index ? { ...item, [field]: value } : item))
    onChange(next)
  }

  function removeSkill(index) {
    onChange(skills.filter((_, idx) => idx !== index))
    setSelectedIndex(null)
  }

  function addSkill() {
    const next = [...(skills || []), emptySubSkill()]
    onChange(next)
    setSelectedIndex(next.length - 1)
  }

  function moveSkill(index, delta) {
    const target = index + delta
    if (target < 0 || target >= skills.length) return
    const next = [...skills]
    ;[next[index], next[target]] = [next[target], next[index]]
    onChange(next)
    setSelectedIndex(target)
  }

  const selectedSkill = selectedIndex != null ? skills[selectedIndex] : null

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <span className="text-sm font-medium text-white">子技能</span>
          <p className="text-xs text-navy-400 mt-0.5">点击卡片编辑；Agent 运行时按顺序调度这些技能</p>
        </div>
        <button
          type="button"
          onClick={addSkill}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gold-300 border border-gold-400/30 hover:bg-gold-400/10"
        >
          <Plus className="w-3.5 h-3.5" />
          添加技能
        </button>
      </div>

      <SubSkillCardGrid
        skills={skills}
        selectedIndex={selectedIndex}
        onSelect={setSelectedIndex}
      />

      {selectedSkill != null && selectedIndex != null ? (
        <SubSkillDetailForm
          skill={selectedSkill}
          onPatch={(field, value) => patchSkill(selectedIndex, field, value)}
          onRemove={() => removeSkill(selectedIndex)}
          onMoveUp={() => moveSkill(selectedIndex, -1)}
          onMoveDown={() => moveSkill(selectedIndex, 1)}
          canMoveUp={selectedIndex > 0}
          canMoveDown={selectedIndex < skills.length - 1}
        />
      ) : skills.length > 0 ? (
        <p className="text-xs text-navy-500 text-center">选择上方卡片以编辑技能详情</p>
      ) : null}
    </div>
  )
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
                  : 'border-white/10 bg-white/[0.03] text-slate-400 hover:border-white/20'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>
      {!catalog.length ? (
        <p className="text-xs text-navy-400">暂无 Tier1 目录</p>
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

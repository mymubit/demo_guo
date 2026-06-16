import { useState, useMemo } from 'react'
import { Quote, User } from 'lucide-react'
import { MetaChip } from './MasterDetailLayout'
import CharacterRelationshipGraph from './CharacterRelationshipGraph'
import { resolveRelationshipList } from '@/utils/relationshipResolve'
import {
  isEnglishSlug,
  resolveArchetypeLabel,
  resolveRelationTypeLabel,
  resolveRoleTypeLabel,
} from '@/utils/displayLabels'

const TAG_COLORS = [
  'bg-rose-500/15 text-rose-200 border-rose-500/25',
  'bg-cyan-500/15 text-cyan-200 border-cyan-500/25',
  'bg-emerald-500/15 text-emerald-200 border-emerald-500/25',
  'bg-amber-500/15 text-amber-200 border-amber-500/25',
  'bg-violet-500/15 text-violet-200 border-violet-500/25',
]

const ROLE_GROUPS = [
  { key: 'protagonists', label: '主角团' },
  { key: 'antagonists', label: '反派' },
  { key: 'supporting', label: '配角' },
]

const PROFILE_TABS = [
  { id: 'profile', label: '档案' },
  { id: 'arc', label: '弧线' },
  { id: 'voice', label: '标志' },
  { id: 'behavior', label: '行为' },
]

function normalizeTag(text) {
  return String(text || '')
    .trim()
    .replace(/^[、，,;；\s]+|[、，,;；\s]+$/g, '')
    .replace(/[。．.!！?？；;]+$/g, '')
    .trim()
}

function splitPersonalityTags(text) {
  if (!text) return []
  const raw = String(text).trim()
  const parts = raw.split(/[、，,;；|/]+/).map(normalizeTag).filter(Boolean)
  if (parts.length > 1) return parts
  const single = normalizeTag(raw)
  return single ? [single] : []
}

export function CharacterMetaStrip({ bible }) {
  const count = bible?.characterCount || bible?.characters?.length || 0
  const relCount = bible?.relationships?.length || 0
  return (
    <div className="flex flex-wrap items-center gap-2">
      <MetaChip>{count} 位角色</MetaChip>
      {relCount > 0 && <MetaChip>{relCount} 组关系</MetaChip>}
    </div>
  )
}

export function buildCharacterNavSections(bible) {
  const sections = []
  const characters = bible?.characters || []
  const groups = bible?.groups || {}
  const hasRelations = (bible?.relationships || []).length > 0 || bible?.relationshipSummary
  const seen = new Set()

  const hasGrouped =
    (groups.protagonists || []).length > 0 ||
    (groups.antagonists || []).length > 0 ||
    (groups.supporting || []).length > 0

  if (hasGrouped) {
    for (const { key, label } of ROLE_GROUPS) {
      const groupChars = groups[key] || []
      if (!groupChars.length) continue
      sections.push({ id: `group-${key}`, label, isGroup: true })
      for (const char of groupChars) {
        const charId = char.id || char.name
        if (!charId || seen.has(charId)) continue
        seen.add(charId)
        sections.push({
          id: `char-${charId}`,
          label: char.name || '未命名',
          subtitle: resolveRoleTypeLabel(char),
          charId,
        })
      }
    }
    for (const char of characters) {
      const charId = char.id || char.name
      if (!charId || seen.has(charId)) continue
      seen.add(charId)
      sections.push({
        id: `char-${charId}`,
        label: char.name || '未命名',
          subtitle: resolveRoleTypeLabel(char),
        charId,
      })
    }
  } else {
    for (const char of characters) {
      const charId = char.id || char.name
      if (!charId) continue
      sections.push({
        id: `char-${charId}`,
        label: char.name || '未命名',
          subtitle: resolveRoleTypeLabel(char),
        charId,
      })
    }
  }

  if (hasRelations) {
    sections.push({
      id: 'relations',
      label: '关系网',
      subtitle: `${(bible?.relationships || []).length || 0} 组`,
    })
  }

  return sections
}

export function CharacterSummaryBanner({ summary, editMode, onChange, inputClass }) {
  if (!summary && !editMode) return null
  const textareaClass =
    inputClass ||
    'sf-control resize-y'

  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3.5">
      <div className="text-[10px] text-gold-400/70 font-medium mb-1.5 tracking-wide">总述</div>
      {editMode ? (
        <textarea
          value={summary || ''}
          onChange={(e) => onChange?.(e.target.value)}
          rows={4}
          className={textareaClass}
          placeholder="角色体系总述：核心人物关系、情感主线与戏剧张力"
        />
      ) : (
        <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{summary}</p>
      )}
    </div>
  )
}

function looksLikeTraitTags(text) {
  const parts = splitPersonalityTags(text)
  if (parts.length <= 1) return false
  const maxLen = Math.max(...parts.map((p) => p.length))
  const avgLen = parts.reduce((sum, p) => sum + p.length, 0) / parts.length
  if (maxLen > 16 || avgLen > 10) return false
  const narrativeRe = /[时在将用了地得着的]/
  if (parts.some((p) => p.length > 8 && narrativeRe.test(p))) return false
  return true
}

function PersonalityBlock({ label, text, colorOffset = 0 }) {
  const value = String(text || '').trim()
  if (!value) return null

  if (looksLikeTraitTags(value)) {
    let colorIdx = colorOffset
    return (
      <div>
        <div className="text-[10px] text-navy-400 mb-1.5">{label}</div>
        <div className="flex flex-wrap gap-1.5">
          {splitPersonalityTags(value).map((tag) => {
            const cls = TAG_COLORS[colorIdx % TAG_COLORS.length]
            colorIdx += 1
            return (
              <span key={`${label}-${tag}`} className={`inline-flex px-2.5 py-1 rounded-lg text-xs border ${cls}`}>
                {tag}
              </span>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="text-[10px] text-navy-400 mb-1.5">{label}</div>
      <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{value}</p>
    </div>
  )
}

function PersonalityTagRow({ surface, real }) {
  const surfaceValue = String(surface || '').trim()
  const realValue = String(real || '').trim()
  if (!surfaceValue && !realValue) return null

  if (!surfaceValue || !realValue) {
    return <PersonalityBlock label="性格" text={surfaceValue || realValue} />
  }

  return (
    <div className="space-y-3">
      <PersonalityBlock label="表面性格" text={surfaceValue} colorOffset={0} />
      <PersonalityBlock label="真实性格" text={realValue} colorOffset={2} />
    </div>
  )
}

function TagList({ items, emptyLabel }) {
  if (!items?.length) return emptyLabel ? <p className="text-sm text-navy-400">{emptyLabel}</p> : null
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <MetaChip key={item}>{item}</MetaChip>
      ))}
    </div>
  )
}

function BehaviorSection({ behavior = {} }) {
  const rows = [
    ['口头禅', behavior.catchphrase],
    ['习惯动作', behavior.habit],
    ['语言风格', behavior.languageStyle],
    ['决策逻辑', behavior.decisionLogic],
    ['行为特征', behavior.behaviorFeatures],
    ['喜好', behavior.likes],
    ['厌恶', behavior.dislikes],
  ].filter(([, val]) => (Array.isArray(val) ? val.length : val))

  if (!rows.length) return <p className="text-sm text-navy-400">暂无行为模式描述</p>

  return (
    <div className="space-y-4">
      {rows.map(([label, val]) => (
        <div key={label}>
          <div className="text-xs text-navy-400 mb-2">{label}</div>
          {Array.isArray(val) ? (
            <TagList items={val} />
          ) : (
            <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{val}</p>
          )}
        </div>
      ))}
    </div>
  )
}

function VisualAnchorSection({ anchor = {} }) {
  const has =
    anchor.distinctiveFeatures ||
    anchor.clothingStyle ||
    anchor.habitGestures ||
    (anchor.consistencyRules || []).length
  if (!has) return null

  return (
    <div className="space-y-3 rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
      <div className="text-xs text-gold-400/80 font-medium">视觉锚定</div>
      <InfoCell label="显著特征" value={anchor.distinctiveFeatures} />
      <InfoCell label="服装风格" value={anchor.clothingStyle} />
      <InfoCell label="习惯动作" value={anchor.habitGestures} />
      {(anchor.consistencyRules || []).length > 0 && (
        <div>
          <div className="text-xs text-navy-400 mb-2">一致性保障</div>
          <ul className="text-sm text-navy-200 space-y-1 list-disc list-inside">
            {anchor.consistencyRules.map((rule) => (
              <li key={rule}>{rule}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function InfoCell({ label, value }) {
  if (!value) return null
  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2.5">
      <div className="text-[10px] text-navy-400 mb-1">{label}</div>
      <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap">{value}</p>
    </div>
  )
}

function FieldEditor({ label, value, onChange, rows = 2 }) {
  const inputClass =
    'sf-control resize-y'
  return (
    <div>
      <div className="text-xs text-navy-400 mb-1.5">{label}</div>
      <textarea value={value || ''} onChange={(e) => onChange?.(e.target.value)} rows={rows} className={inputClass} />
    </div>
  )
}

function ArcTimeline({ arc }) {
  if (!arc?.startingState && !arc?.finalState && !(arc?.keyTurningPoints || []).length) {
    return <p className="text-sm text-navy-400">暂无弧线描述</p>
  }
  const steps = [
    arc.startingState ? { label: '起点', text: arc.startingState } : null,
    ...(arc.keyTurningPoints || []).map((text, i) => ({ label: `转折 ${i + 1}`, text })),
    arc.finalState ? { label: '终点', text: arc.finalState } : null,
  ].filter(Boolean)

  return (
    <div className="relative pl-4 border-l border-gold-400/25 space-y-4">
      {steps.map((step, i) => (
        <div key={`${step.label}-${i}`} className="relative">
          <span className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-gold-400/80 ring-4 ring-slate-900/80" />
          <div className="text-[10px] text-gold-400/70 font-medium mb-0.5">{step.label}</div>
          <p className="text-sm text-navy-100 leading-relaxed">{step.text}</p>
        </div>
      ))}
    </div>
  )
}

export function CharacterOverviewPanel({ bible, onSelectCharacter }) {
  const characters = bible?.characters || []
  if (!characters.length) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
      {characters.map((char) => {
        const charId = char.id || char.name
        const oneLiner = char.oneLineSummary || char.coreMotivation || ''
        return (
          <button
            key={charId}
            type="button"
            onClick={() => onSelectCharacter?.(`char-${charId}`)}
            className="text-left rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 transition-colors hover:border-gold-400/35 hover:bg-gold-400/5"
          >
            <div className="flex items-center gap-2 mb-1">
              <User className="w-3.5 h-3.5 text-gold-400/70 shrink-0" />
              <span className="text-sm font-medium text-white truncate">{char.name}</span>
              {resolveRoleTypeLabel(char) && (
                <span className="text-[10px] text-navy-400 shrink-0">{resolveRoleTypeLabel(char)}</span>
              )}
            </div>
            {oneLiner && (
              <p className="text-xs text-navy-400 line-clamp-2 leading-relaxed">{oneLiner}</p>
            )}
          </button>
        )
      })}
    </div>
  )
}

export function CharacterProfilePanel({ char, bible, editMode, onChange }) {
  const [tab, setTab] = useState('profile')
  const arc = char?.characterArc || {}
  const inputClass =
    'sf-control'

  if (editMode) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <div className="text-xs text-navy-400 mb-1.5">姓名</div>
            <div className={`${inputClass} bg-slate-900/40 text-navy-100 opacity-80`}>{char.name}</div>
          </div>
          <div>
            <div className="text-xs text-navy-400 mb-1.5">定位</div>
            <div className={`${inputClass} bg-slate-900/40 text-navy-100`}>
              {resolveRoleTypeLabel(char) || '—'}
            </div>
          </div>
          <FieldEditor label="表面性格" value={char.surfacePersonality} onChange={(v) => onChange?.('surfacePersonality', v)} />
        </div>
        <FieldEditor label="真实性格" value={char.realPersonality} onChange={(v) => onChange?.('realPersonality', v)} />
        <FieldEditor label="背景" value={char.background} onChange={(v) => onChange?.('background', v)} rows={5} />
        <FieldEditor label="核心动机" value={char.coreMotivation} onChange={(v) => onChange?.('coreMotivation', v)} />
        <FieldEditor label="短期目标" value={char.shortTermGoal} onChange={(v) => onChange?.('shortTermGoal', v)} />
        <FieldEditor label="长期目标" value={char.longTermGoal} onChange={(v) => onChange?.('longTermGoal', v)} />
        <FieldEditor label="隐藏秘密" value={char.secret} onChange={(v) => onChange?.('secret', v)} />
        <FieldEditor label="软肋" value={char.weakness} onChange={(v) => onChange?.('weakness', v)} />
        <FieldEditor label="外貌" value={char.appearance} onChange={(v) => onChange?.('appearance', v)} rows={3} />
        <div>
          <div className="text-xs text-navy-400 mb-1.5">代表台词（每行一条）</div>
          <textarea
            value={(char.signatureLines || []).join('\n')}
            onChange={(e) =>
              onChange?.(
                'signatureLines',
                e.target.value.split('\n').map((l) => l.trim()).filter(Boolean)
              )
            }
            rows={3}
            className={`${inputClass} resize-y`}
          />
        </div>
        <FieldEditor
          label="台词风格"
          value={char.signatureDialogueStyle}
          onChange={(v) => onChange?.('signatureDialogueStyle', v)}
        />
        <div>
          <div className="text-xs text-navy-400 mb-1.5">说话模式（每行一条）</div>
          <textarea
            value={(char.speechPatterns || []).join('\n')}
            onChange={(e) =>
              onChange?.(
                'speechPatterns',
                e.target.value.split('\n').map((l) => l.trim()).filter(Boolean)
              )
            }
            rows={2}
            className={`${inputClass} resize-y`}
          />
        </div>
        <div>
          <div className="text-xs text-navy-400 mb-1.5">标志性道具（每行一条）</div>
          <textarea
            value={(char.iconicProps || []).join('\n')}
            onChange={(e) =>
              onChange?.(
                'iconicProps',
                e.target.value.split('\n').map((l) => l.trim()).filter(Boolean)
              )
            }
            rows={2}
            className={`${inputClass} resize-y`}
          />
        </div>
        <div className="space-y-3 rounded-xl border border-white/5 p-4">
          <div className="text-xs text-gold-400/80">角色弧线</div>
          <FieldEditor
            label="起点"
            value={arc.startingState}
            onChange={(v) => onChange?.('characterArc', { ...arc, startingState: v })}
          />
          <div>
            <div className="text-xs text-navy-400 mb-1.5">转折点（每行一条）</div>
            <textarea
              value={(arc.keyTurningPoints || []).join('\n')}
              onChange={(e) =>
                onChange?.('characterArc', {
                  ...arc,
                  keyTurningPoints: e.target.value.split('\n').map((l) => l.trim()).filter(Boolean),
                })
              }
              rows={3}
              className={`${inputClass} resize-y`}
            />
          </div>
          <FieldEditor
            label="终点"
            value={arc.finalState}
            onChange={(v) => onChange?.('characterArc', { ...arc, finalState: v })}
          />
        </div>
      </div>
    )
  }

  const oneLiner = char.oneLineSummary || char.coreMotivation || ''
  const hasArc =
    arc.startingState || arc.finalState || (arc.keyTurningPoints || []).length > 0
  const hasVoice =
    (char.signatureLines || []).length > 0 ||
    char.signatureDialogueStyle ||
    (char.speechPatterns || []).length > 0 ||
    (char.iconicProps || []).length > 0 ||
    char.voiceProfile?.summary ||
    char.voiceProfile?.label
  const hasBehavior =
    char.behaviorProfile?.catchphrase ||
    char.behaviorProfile?.habit ||
    (char.behaviorProfile?.languageStyle || []).length > 0 ||
    (char.behaviorProfile?.decisionLogic || []).length > 0 ||
    (char.behaviorProfile?.behaviorFeatures || []).length > 0 ||
    (char.behaviorProfile?.likes || []).length > 0 ||
    (char.behaviorProfile?.dislikes || []).length > 0
  const hasVisual =
    char.visualAnchor?.distinctiveFeatures ||
    char.visualAnchor?.clothingStyle ||
    (char.visualAnchor?.consistencyRules || []).length > 0

  const visibleTabs = PROFILE_TABS.filter((t) => {
    if (t.id === 'arc') return hasArc
    if (t.id === 'voice') return hasVoice || hasVisual
    if (t.id === 'behavior') return hasBehavior
    return true
  })

  const activeTab = visibleTabs.some((t) => t.id === tab) ? tab : visibleTabs[0]?.id || 'profile'
  const roleLabel = resolveRoleTypeLabel(char)
  const archetypeLabel = resolveArchetypeLabel(char, bible)

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gold-400/20 bg-gradient-to-br from-slate-900/80 to-slate-950/60 px-4 py-4">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {roleLabel ? <MetaChip className="text-gold-300/90">{roleLabel}</MetaChip> : null}
          {archetypeLabel ? <MetaChip>{archetypeLabel}</MetaChip> : null}
          {char.age != null && <MetaChip>{char.age} 岁</MetaChip>}
          {char.genderLabel && <MetaChip>{char.genderLabel}</MetaChip>}
        </div>
        {oneLiner && <p className="text-sm text-navy-100 leading-relaxed">{oneLiner}</p>}
      </div>

      {visibleTabs.length > 1 && (
        <div className="flex w-fit gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-1">
          {visibleTabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === t.id
                  ? 'bg-gold-400/15 text-gold-200'
                  : 'text-navy-400 hover:text-navy-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      {activeTab === 'profile' && (
        <div className="space-y-4">
          <div>
            <div className="text-xs text-navy-400 mb-2">性格</div>
            <PersonalityTagRow surface={char.surfacePersonality} real={char.realPersonality} />
            {!char.surfacePersonality && !char.realPersonality && char.personality ? (
              <p className="text-sm text-navy-100 leading-relaxed whitespace-pre-wrap mt-2">
                {char.personality}
              </p>
            ) : null}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            <InfoCell label="核心动机" value={char.coreMotivation} />
            <InfoCell label="短期目标" value={char.shortTermGoal} />
            <InfoCell label="长期目标" value={char.longTermGoal} />
            <InfoCell label="隐藏秘密" value={char.secret} />
            <InfoCell label="软肋" value={char.weakness} />
            <InfoCell label="外貌" value={char.appearance} />
          </div>
          <InfoCell label="背景" value={char.background} />
          {char.contrastRelation?.contrastType || char.contrastRelation?.contrastDescription ? (
            <div className="rounded-xl border border-violet-500/15 bg-violet-500/5 px-3 py-3">
              <div className="text-xs text-violet-300/80 mb-1">对照关系</div>
              {char.contrastRelation.contrastType ? (
                <MetaChip className="mb-2">{char.contrastRelation.contrastType}</MetaChip>
              ) : null}
              <p className="text-sm text-navy-100 leading-relaxed">
                {char.contrastRelation.contrastDescription}
              </p>
            </div>
          ) : null}
        </div>
      )}

      {activeTab === 'arc' && <ArcTimeline arc={arc} />}

      {activeTab === 'voice' && (
        <div className="space-y-4">
          {char.voiceProfile?.summary || char.voiceProfile?.label ? (
            <div className="rounded-xl border border-cyan-500/15 bg-cyan-500/5 px-4 py-3">
              <div className="text-xs text-cyan-300/80 mb-1">配音音色</div>
              <p className="text-sm text-navy-100 leading-relaxed">
                {char.voiceProfile.summary ||
                  `${char.voiceProfile.label}（音高${char.voiceProfile.pitch || '中'} · 语速${char.voiceProfile.pace || '中'}）`}
              </p>
            </div>
          ) : null}
          <VisualAnchorSection anchor={char.visualAnchor} />
          {(char.signatureLines || []).length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs text-navy-400 mb-2">
                <Quote className="w-3.5 h-3.5" />
                代表台词
              </div>
              <ul className="space-y-1.5">
                {char.signatureLines.map((line, i) => (
                  <li key={i} className="text-sm text-navy-100 italic">
                    「{line}」
                  </li>
                ))}
              </ul>
            </div>
          )}
          <InfoCell label="台词风格" value={char.signatureDialogueStyle} />
          {(char.speechPatterns || []).length > 0 && (
            <div>
              <div className="text-xs text-navy-400 mb-2">说话模式</div>
              <div className="flex flex-wrap gap-1.5">
                {char.speechPatterns.map((pattern) => (
                  <MetaChip key={pattern}>{pattern}</MetaChip>
                ))}
              </div>
            </div>
          )}
          {(char.iconicProps || []).length > 0 && (
            <div>
              <div className="text-xs text-navy-400 mb-2">标志性道具</div>
              <div className="flex flex-wrap gap-1.5">
                {char.iconicProps.map((prop) => (
                  <MetaChip key={prop}>{prop}</MetaChip>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'behavior' && <BehaviorSection behavior={char.behaviorProfile} />}
    </div>
  )
}

export function CharacterArchetypePanel({ bible }) {
  const index = bible?.archetypeIndex || {}
  const codes = bible?.archetypeCodes || []
  const entries = Object.entries(index).filter(([, label]) => label)
  if (!entries.length && !codes.length) return null

  return (
    <div className="space-y-4">
      {codes.some((code) => index[code]) ? (
        <div className="flex flex-wrap gap-1.5">
          {codes.map((code) => {
            const label = index[code]
            if (!label) return null
            return (
              <MetaChip key={code} className="text-gold-300/90">
                {label}
              </MetaChip>
            )
          })}
        </div>
      ) : null}
      {entries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {entries.map(([code, label]) => (
            <div
              key={code}
              className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3"
            >
              <div className="text-sm text-navy-100 leading-relaxed">{label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function relationshipDedupKey(rel) {
  const a = (rel.characterAName || rel.characterAId || '').trim()
  const b = (rel.characterBName || rel.characterBId || '').trim()
  const pair = [a, b].filter(Boolean).sort().join('|')
  const rtype = resolveRelationTypeLabel(rel)
  const desc = (rel.description || '').trim().slice(0, 120)
  return `${pair}::${rtype}::${desc}`
}

function dedupeRelationships(rows) {
  const seen = new Set()
  const out = []
  for (const rel of rows || []) {
    const key = relationshipDedupKey(rel)
    if (seen.has(key)) continue
    seen.add(key)
    out.push(rel)
  }
  return out
}

export function CharacterCreativeDnaPanel({ bible }) {
  const dna = bible?.creativeDna || {}
  const anti = dna.antiClicheElements || []
  const unique = dna.uniqueSettings || []
  const notes = dna.aiAuthenticityNotes || []
  if (!anti.length && !unique.length && !notes.length) return null

  return (
    <div className="space-y-4">
      {anti.length > 0 && (
        <div className="rounded-2xl border border-white/5 bg-slate-900/40 overflow-hidden">
          <div className="border-b border-white/5 bg-slate-900/60 px-4 py-2.5 text-xs font-medium text-gold-400/85">
            反套路元素
          </div>
          <div className="p-4 space-y-3">
            {anti.map((item, i) => (
              <div key={`${item.code}-${i}`} className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  {item.code && !isEnglishSlug(item.code) ? <MetaChip>{item.code}</MetaChip> : null}
                  <span className="text-sm font-medium text-white">{item.label}</span>
                </div>
                {item.effect ? <p className="text-xs text-navy-300 leading-relaxed">{item.effect}</p> : null}
              </div>
            ))}
          </div>
        </div>
      )}
      {unique.length > 0 && (
        <div className="rounded-2xl border border-white/5 bg-slate-900/40 overflow-hidden">
          <div className="border-b border-white/5 bg-slate-900/60 px-4 py-2.5 text-xs font-medium text-gold-400/85">
            独特设定
          </div>
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {unique.map((item, i) => (
              <div key={`${item.code}-${i}`} className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-3">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  {item.code && !isEnglishSlug(item.code) ? <MetaChip>{item.code}</MetaChip> : null}
                  <span className="text-sm text-gold-300/90">{item.label}</span>
                </div>
                {item.example ? <p className="text-xs text-navy-300 leading-relaxed">{item.example}</p> : null}
              </div>
            ))}
          </div>
        </div>
      )}
      {notes.length > 0 && (
        <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
          <div className="text-xs text-gold-400/80 font-medium mb-2">AI 痕迹预防</div>
          <ul className="text-sm text-navy-200 space-y-1.5 list-disc list-inside">
            {notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function RelationshipMatrixRow({ rel, onSelectCharacter }) {
  const { displayA, displayB, charAId, charBId } = rel
  const hasMatrix = rel.perspectiveA || rel.perspectiveB || rel.coreConflict || rel.hiddenTension

  return (
    <li className="rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2.5 text-sm">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mb-1">
        <button
          type="button"
          onClick={() => charAId && onSelectCharacter?.(`char-${charAId}`)}
          className="text-gold-300/90 hover:underline font-medium"
        >
          {displayA}
        </button>
        <span className="text-navy-500">↔</span>
        <button
          type="button"
          onClick={() => charBId && onSelectCharacter?.(`char-${charBId}`)}
          className="text-gold-300/90 hover:underline font-medium"
        >
          {displayB}
        </button>
        {resolveRelationTypeLabel(rel) ? <MetaChip>{resolveRelationTypeLabel(rel)}</MetaChip> : null}
      </div>
      <p className="text-xs text-navy-300 leading-relaxed">{rel.description}</p>
      {hasMatrix ? (
        <div className="mt-2.5 overflow-hidden rounded-lg border border-white/5 bg-slate-900/40 text-[11px]">
          <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/10">
            {rel.perspectiveA ? (
              <div className="px-3 py-2">
                <span className="text-navy-400">{displayA} → {displayB}：</span>
                <span className="text-navy-200">{rel.perspectiveA}</span>
              </div>
            ) : null}
            {rel.perspectiveB ? (
              <div className="px-3 py-2">
                <span className="text-navy-400">{displayB} → {displayA}：</span>
                <span className="text-navy-200">{rel.perspectiveB}</span>
              </div>
            ) : null}
          </div>
          {rel.coreConflict ? (
            <div className="px-3 py-2 border-t border-white/5">
              <span className="text-amber-400/80">核心冲突：</span>
              <span className="text-navy-200">{rel.coreConflict}</span>
            </div>
          ) : null}
          {rel.hiddenTension ? (
            <div className="px-3 py-2 border-t border-white/5">
              <span className="text-violet-300/80">潜在矛盾：</span>
              <span className="text-navy-200">{rel.hiddenTension}</span>
            </div>
          ) : null}
        </div>
      ) : null}
      {rel.evolutionPath ? (
        <p className="text-[11px] text-navy-400 mt-1.5 leading-relaxed">
          <span className="text-navy-500">演化：</span>
          {rel.evolutionPath}
        </p>
      ) : null}
    </li>
  )
}

export function CharacterRelationsPanel({ bible, onSelectCharacter }) {
  const characters = bible?.characters || []
  const relationships = useMemo(
    () => resolveRelationshipList(dedupeRelationships(bible?.relationships || []), characters),
    [bible?.relationships, characters]
  )

  return (
    <div className="space-y-4">
      {bible?.relationshipSummary ? (
        <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
          <div className="text-[10px] text-gold-400/70 font-medium mb-1.5">关系总述</div>
          <p className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed">
            {bible.relationshipSummary}
          </p>
        </div>
      ) : null}
      <CharacterRelationshipGraph
        characters={characters}
        relationships={relationships}
        onSelectCharacter={(id) => onSelectCharacter?.(`char-${id}`)}
      />
      {relationships.length > 0 ? (
        <ul className="space-y-2 border-t border-white/5 pt-4">
          {relationships.map((rel, i) => (
            <RelationshipMatrixRow
              key={`${rel.characterAName}-${rel.characterBName}-${i}`}
              rel={rel}
              onSelectCharacter={onSelectCharacter}
            />
          ))}
        </ul>
      ) : (
        <p className="text-sm text-navy-300 whitespace-pre-wrap leading-relaxed">
          {bible?.relationshipSummary || '—'}
        </p>
      )}
    </div>
  )
}

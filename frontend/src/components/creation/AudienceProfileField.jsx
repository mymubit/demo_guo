import { Users } from 'lucide-react'
import { toast } from 'sonner'
import AiGenerateButton from '@/components/creation/AiGenerateButton'
import {
  AUDIENCE_AGE_PRESETS,
  AUDIENCE_PREF_PRESETS,
  parseAudienceProfile,
  serializeAudienceProfile,
  togglePreference,
} from '@/utils/audienceProfile'

export default function AudienceProfileField({
  profile,
  onChange,
  currencyName,
  actionCost,
  actionRequiresMember,
  membershipActive,
  aiContext,
  disabled,
}) {
  const ageRange = profile?.ageRange || ''
  const preferences = profile?.preferences || []
  const note = profile?.note || ''

  function emit(next) {
    onChange(next, serializeAudienceProfile(next))
  }

  function applyAi(text) {
    if (!text?.trim()) {
      toast.error('AI 未返回有效内容，请重试')
      return
    }
    emit(parseAudienceProfile(text))
  }

  const hasContent = ageRange || preferences.length || note

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-navy-400">先选标签，AI 会按字段补全画像</p>
        <AiGenerateButton
          actionKey="ai.generate.audience"
          coinCost={actionCost?.('ai.generate.audience', 10) ?? 10}
          currencyName={currencyName}
          label="AI 生成画像"
          memberOnly={actionRequiresMember?.('ai.generate.audience')}
          membershipActive={membershipActive}
          context={aiContext()}
          disabled={disabled}
          onGenerated={applyAi}
        />
      </div>

      <div>
        <div className="text-xs font-medium text-navy-300 mb-2">年龄段 / 人群</div>
        <div className="flex flex-wrap gap-2 mb-2">
          {AUDIENCE_AGE_PRESETS.map((age) => {
            const active = ageRange === age
            return (
              <button
                key={age}
                type="button"
                onClick={() => emit({ ageRange: active ? '' : age, preferences, note })}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                  active
                    ? 'bg-gold-400/20 text-gold-400 ring-1 ring-gold-400/40'
                    : 'bg-navy-800/50 text-navy-300 hover:bg-navy-700/40'
                }`}
              >
                {age}
              </button>
            )
          })}
        </div>
        <input
          value={ageRange}
          onChange={(e) => emit({ ageRange: e.target.value.slice(0, 40), preferences, note })}
          placeholder="或自定义，如：25-45岁职场女性"
          className="w-full px-3 py-2 rounded-lg bg-navy-900/50 border border-navy-700/40 text-white text-sm placeholder-navy-500 focus:border-gold-400/40 outline-none"
        />
      </div>

      <div>
        <div className="text-xs font-medium text-navy-300 mb-2">内容偏好</div>
        <div className="flex flex-wrap gap-2">
          {AUDIENCE_PREF_PRESETS.map((tag) => {
            const active = preferences.includes(tag)
            return (
              <button
                key={tag}
                type="button"
                onClick={() =>
                  emit({
                    ageRange,
                    preferences: togglePreference(preferences, tag),
                    note,
                  })
                }
                className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                  active
                    ? 'bg-purple-500/20 text-purple-200 ring-1 ring-purple-400/40'
                    : 'bg-navy-800/50 text-navy-300 hover:bg-navy-700/40'
                }`}
              >
                {tag}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <div className="text-xs font-medium text-navy-300 mb-2">画像描述</div>
        {hasContent && !note ? (
          <div className="rounded-xl border border-navy-700/40 bg-navy-900/30 px-4 py-3 text-xs text-navy-400">
            已选标签，可补充一句观看动机（可选）
          </div>
        ) : null}
        <textarea
          value={note}
          onChange={(e) => emit({ ageRange, preferences, note: e.target.value.slice(0, 400) })}
          placeholder="例：渴望情绪宣泄，偏好高智商大女主，不喜欢傻白甜人设…"
          rows={4}
          className="w-full min-h-[96px] p-4 rounded-xl bg-navy-900/50 border border-navy-600/30 text-white text-sm leading-relaxed placeholder-navy-500 focus:border-gold-400/50 outline-none resize-y"
        />
        <p className="text-[11px] text-navy-500 mt-1 text-right">{note.length}/400</p>
      </div>
    </div>
  )
}

/** 简报页只读展示 */
export function AudienceProfileSummary({ profile, fallbackText }) {
  const p =
    profile?.ageRange || profile?.preferences?.length || profile?.note
      ? profile
      : parseAudienceProfile(fallbackText)

  if (!p.ageRange && !p.preferences?.length && !p.note) return null

  return (
    <div className="rounded-xl bg-navy-800/40 border border-navy-600/20 p-4 space-y-3">
      {p.ageRange ? (
        <div className="flex items-start gap-2 text-sm">
          <Users className="w-4 h-4 text-gold-400 shrink-0 mt-0.5" />
          <span className="text-white font-medium">{p.ageRange}</span>
        </div>
      ) : null}
      {p.preferences?.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {p.preferences.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-200 text-xs"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}
      {p.note ? <p className="text-sm text-navy-200 leading-relaxed">{p.note}</p> : null}
    </div>
  )
}

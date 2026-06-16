import { Sparkles } from 'lucide-react'
import AiGenerateButton from '@/components/creation/AiGenerateButton'
import { EMOTIONAL_TONE_PRESETS, parseInspirationPlan } from '@/utils/storyBrief'

function FieldLabel({ title, hint, required }) {
  return (
    <div className="mb-2">
      <label className="text-sm font-medium text-white">
        {title}
        {required ? <span className="text-red-400 ml-0.5">*</span> : null}
      </label>
      {hint ? <p className="text-xs text-navy-400 mt-0.5">{hint}</p> : null}
    </div>
  )
}

export default function StoryBriefFields({
  formData,
  onChange,
  currencyName,
  actionCost,
  actionRequiresMember,
  membershipActive,
  aiContext,
  disabled,
}) {
  const update = (key, value) => onChange(key, value)

  function applyInspirationPlan(text) {
    const parsed = parseInspirationPlan(text)
    onChange('batch', parsed)
  }

  const hookLen = (formData.idea || '').length
  const hookOk = hookLen >= 20

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-navy-400">根据上方题材、集数、平台等参数生成</p>
        <AiGenerateButton
          actionKey="ai.generate.inspiration_plan"
          coinCost={actionCost?.('ai.generate.inspiration_plan', 30) ?? 30}
          currencyName={currencyName}
          label="灵感策划"
          memberOnly={actionRequiresMember?.('ai.generate.inspiration_plan') ?? true}
          membershipActive={membershipActive}
          context={aiContext()}
          disabled={disabled}
          onGenerated={applyInspirationPlan}
        />
      </div>

      <div>
        <FieldLabel title="一句话梗概" hint="80–150 字，概括主角与核心卖点" required />
        <div className="relative">
          <textarea
            value={formData.idea}
            onChange={(e) => update('idea', e.target.value.slice(0, 200))}
            placeholder="例：落难千金与毁容总裁闪婚，她以为只是交易，却不知他才是当年救她的人…"
            className="sf-control h-24 resize-none leading-relaxed"
          />
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            <AiGenerateButton
              actionKey="ai.generate.core_idea"
              coinCost={actionCost?.('ai.generate.core_idea', 20) ?? 20}
              currencyName={currencyName}
              memberOnly={actionRequiresMember?.('ai.generate.core_idea')}
              membershipActive={membershipActive}
              context={aiContext()}
              disabled={disabled}
              onGenerated={(text) => update('idea', text.trim().slice(0, 200))}
              className="scale-90 origin-right"
            />
            <span className={`text-xs ${hookOk ? 'text-green-400' : 'text-navy-400'}`}>
              {hookLen}/200
            </span>
          </div>
        </div>
      </div>

      <div>
        <FieldLabel title="核心冲突" hint="主角与对立面的主要矛盾" required />
        <textarea
          value={formData.coreConflict}
          onChange={(e) => update('coreConflict', e.target.value.slice(0, 300))}
          placeholder="例：女主为复仇接近男主，却发现真相与记忆完全相反…"
          className="sf-control h-24 resize-none leading-relaxed"
        />
      </div>

      <div>
        <FieldLabel title="情绪基调" hint="选择或补充整剧情绪走向" required />
        <div className="flex flex-wrap gap-2 mb-2">
          {EMOTIONAL_TONE_PRESETS.map((tone) => {
            const active = formData.emotionalTone === tone
            return (
              <button
                key={tone}
                type="button"
                onClick={() => update('emotionalTone', tone)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                  active
                    ? 'bg-gold-400/20 text-gold-400 ring-1 ring-gold-400/40'
                    : 'border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20'
                }`}
              >
                {tone}
              </button>
            )
          })}
        </div>
        <input
          value={formData.emotionalTone}
          onChange={(e) => update('emotionalTone', e.target.value.slice(0, 80))}
          placeholder="或自定义，如：先虐后甜、身份反转密集"
          className="sf-control"
        />
      </div>

      <div>
        <FieldLabel title="前三集钩子" hint="开篇如何抓住观众（可选）" />
        <textarea
          value={formData.openingHooks}
          onChange={(e) => update('openingHooks', e.target.value.slice(0, 400))}
          placeholder={'第1集：…\n第2集：…\n第3集：…'}
          className="sf-control h-28 resize-none leading-relaxed"
        />
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs text-navy-400 pt-1">
        <span className="flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-purple-400" />
          填「梗概」或「冲突+基调」即可继续
        </span>
      </div>
    </div>
  )
}

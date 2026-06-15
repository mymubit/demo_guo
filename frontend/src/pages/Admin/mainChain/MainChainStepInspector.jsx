import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import { COIN_PRICING_NOTE } from '@/utils/adminEconomics'
import { resolveAgentId } from '@/utils/agentTerm'
import { SubSkillEditor, Tier1SectionPicker } from '@/components/admin/AgentConfigEditors'

const inputCls =
  'mt-1 w-full rounded-xl bg-navy-950 border border-navy-700 px-3 py-2 text-white text-sm focus:border-gold-500/40 outline-none'
const textareaCls = `${inputCls} font-mono text-xs min-h-[88px]`

export default function MainChainStepInspector({
  step,
  tier1Catalog = [],
  llmProviders = [],
  onPatch,
  onSave,
  saving = false,
  dirty = false,
}) {
  const [draft, setDraft] = useState(step || null)

  useEffect(() => {
    setDraft(step || null)
  }, [step?.id, step?.node_id])

  const agentId = resolveAgentId(draft || {})

  function patch(field, value) {
    if (!draft) return
    const next = { ...draft, [field]: value }
    setDraft(next)
    onPatch?.(next)
  }

  if (!draft) {
    return (
      <div className="flex items-center justify-center h-full min-h-[320px] text-sm text-navy-500">
        点击左侧步骤或上方画布节点进行配置
      </div>
    )
  }

  const isPipelineTail = (draft.node_index || 0) > 5

  const providerOptions = llmProviders.filter((p) => p.is_enabled)

  return (
    <div className="space-y-5 pb-4">
      {isPipelineTail ? (
        <div className="rounded-xl border border-violet-500/25 bg-violet-500/10 px-4 py-3 text-xs text-violet-200/90 leading-relaxed">
          此步骤属于<strong className="font-medium text-violet-100">分步掌控</strong>管线尾部（fusion_review / fusion_score）。
          技能工作台模式下不会单独触发该节点，质检与评分由下方「后处理链」在剧本全量生成后统一执行。
        </div>
      ) : null}
      <div>
        <div className="text-lg font-semibold text-white">
          {draft.agent_name_zh || draft.display_name || draft.node_id}
        </div>
        <div className="text-xs text-navy-500 mt-1 font-mono">
          {draft.agent_name || agentId || '—'} · {draft.node_id}
        </div>
      </div>

      <section className="rounded-xl bg-navy-900/30 border border-gold-500/15 p-4 space-y-3">
        <div className="text-sm font-medium text-gold-300">运营</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block text-sm text-navy-300">
            单步币价
            <input
              type="number"
              min={0}
              className={inputCls}
              value={draft.coin_cost ?? 0}
              onChange={(e) => patch('coin_cost', Number(e.target.value) || 0)}
            />
          </label>
          <label className="block text-sm text-navy-300">
            C 端展示名
            <input
              className={inputCls}
              value={draft.display_name || ''}
              onChange={(e) => patch('display_name', e.target.value)}
            />
          </label>
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-navy-200">
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!draft.enabled}
              onChange={(e) => patch('enabled', e.target.checked)}
            />
            启用
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!draft.requires_confirm}
              onChange={(e) => patch('requires_confirm', e.target.checked)}
            />
            需用户确认
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={draft.portal_visible !== false}
              onChange={(e) => patch('portal_visible', e.target.checked)}
            />
            C 端主链展示
          </label>
        </div>
        <p className="text-[11px] text-navy-500">{COIN_PRICING_NOTE}</p>
      </section>

      <section className="rounded-xl bg-navy-900/30 border border-emerald-500/15 p-4 space-y-3">
        <div className="text-sm font-medium text-emerald-300">Prompt</div>
        <label className="flex items-center gap-2 text-sm text-navy-300">
          <input
            type="checkbox"
            checked={draft.prompt_enabled !== false}
            onChange={(e) => patch('prompt_enabled', e.target.checked)}
          />
          启用 Prompt
        </label>
        <label className="block text-sm text-navy-300">
          System
          <textarea
            className={textareaCls}
            value={draft.system_prompt || ''}
            onChange={(e) => patch('system_prompt', e.target.value)}
            spellCheck={false}
          />
        </label>
        <label className="block text-sm text-navy-300">
          User 模板
          <textarea
            className={textareaCls}
            value={draft.user_prompt_tpl || ''}
            onChange={(e) => patch('user_prompt_tpl', e.target.value)}
            spellCheck={false}
          />
        </label>
        <label className="block text-sm text-navy-300">
          约束 constraints
          <textarea
            className={`${textareaCls} min-h-[64px]`}
            value={draft.constraints || ''}
            onChange={(e) => patch('constraints', e.target.value)}
            spellCheck={false}
          />
        </label>
      </section>

      <section className="rounded-xl bg-navy-900/30 border border-blue-500/15 p-4 space-y-3">
        <div className="text-sm font-medium text-blue-200">Tier1 分区</div>
        <Tier1SectionPicker
          catalog={tier1Catalog}
          selected={draft.tier1_sections || []}
          onChange={(sections) => patch('tier1_sections', sections)}
        />
      </section>

      <section className="rounded-xl bg-navy-900/30 border border-cyan-500/15 p-4 space-y-3">
        <div className="text-sm font-medium text-cyan-200">子技能链</div>
        <SubSkillEditor
          skills={draft.sub_skills || []}
          onChange={(skills) => patch('sub_skills', skills)}
        />
      </section>

      <section className="rounded-xl bg-navy-900/30 border border-purple-500/15 p-4 space-y-3">
        <div className="text-sm font-medium text-purple-200">模型路由</div>
        <label className="block text-sm text-navy-300">
          Max Tokens
          <input
            type="number"
            min={256}
            step={256}
            className={inputCls}
            value={draft.max_tokens ?? draft.route_max_tokens ?? ''}
            onChange={(e) =>
              patch('max_tokens', e.target.value === '' ? null : Number(e.target.value))
            }
          />
        </label>
        <label className="block text-sm text-navy-300">
          使用大模型
          <select
            className={inputCls}
            value={draft.llm_provider_id || ''}
            onChange={(e) => patch('llm_provider_id', e.target.value || null)}
          >
            <option value="">跟随全局激活模型</option>
            {providerOptions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
                {p.is_active ? '（当前全局）' : ''}
              </option>
            ))}
          </select>
        </label>
      </section>

      <div className="flex items-center justify-between gap-3 pt-2 border-t border-navy-700/40 sticky bottom-0 bg-navy-950/80 backdrop-blur py-2">
        <span className={`text-xs ${dirty ? 'text-amber-300' : 'text-emerald-400/90'}`}>
          {dirty ? '有未保存修改' : '已同步'}
        </span>
        <button
          type="button"
          disabled={!dirty || saving}
          onClick={() => onSave?.(draft)}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-40"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '保存步骤'}
        </button>
      </div>
    </div>
  )
}

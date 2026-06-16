import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Save } from 'lucide-react'
import { AdminInspectorSection } from '@/components/admin/AdminUI'
import { COIN_PRICING_NOTE } from '@/utils/adminEconomics'
import { resolveAgentId } from '@/utils/agentTerm'
import { SubSkillCardGrid, Tier1SectionPicker } from '@/components/admin/AgentConfigEditors'
import { cn } from '@/utils/cn'

const fieldCls = 'sf-control mt-1.5'
const fieldNarrow = cn(fieldCls, 'max-w-[10rem]')
const fieldMedium = cn(fieldCls, 'max-w-md')
const textareaCls = cn(fieldCls, 'font-mono text-xs min-h-[88px] max-w-none')

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
      <div className="flex flex-col items-center justify-center h-full min-h-[360px] text-center px-6">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03]">
          <span className="text-lg text-navy-400">←</span>
        </div>
        <p className="text-sm text-navy-400">从左侧选择流水线步骤</p>
        <p className="text-xs text-navy-400 mt-1">配置 Prompt、模型与子技能</p>
      </div>
    )
  }

  const isPipelineTail = (draft.node_index || 0) > 5
  const providerOptions = llmProviders.filter((p) => p.is_enabled)

  return (
    <div className="space-y-4 pb-4 max-w-3xl">
      {isPipelineTail ? (
        <p className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2.5 text-xs leading-relaxed text-navy-400">
          分步掌控模式的管线尾部节点；工作台模式下由下方「后处理链」统一执行质检与评分。
        </p>
      ) : null}

      <div className="pb-1 border-b border-white/5">
        <div className="text-base font-semibold text-white">
          {draft.agent_name_zh || draft.display_name || draft.node_id}
        </div>
        <div className="text-xs text-navy-300 mt-1 font-mono">
          {draft.agent_name || agentId || '—'} · {draft.node_id}
        </div>
      </div>

      <AdminInspectorSection title="运营与展示">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block">
            <span className="sf-label">单步币价</span>
            <input
              type="number"
              min={0}
              className={fieldNarrow}
              value={draft.coin_cost ?? 0}
              onChange={(e) => patch('coin_cost', Number(e.target.value) || 0)}
            />
          </label>
          <label className="block sm:col-span-1">
            <span className="sf-label">C 端展示名</span>
            <input
              className={fieldMedium}
              value={draft.display_name || ''}
              onChange={(e) => patch('display_name', e.target.value)}
            />
          </label>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-navy-200">
          <label className="inline-flex items-center gap-2">
            <input type="checkbox" checked={!!draft.enabled} onChange={(e) => patch('enabled', e.target.checked)} />
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
        <p className="sf-help-text">{COIN_PRICING_NOTE}</p>
      </AdminInspectorSection>

      <AdminInspectorSection title="Prompt">
        <label className="inline-flex items-center gap-2 text-sm text-navy-200">
          <input
            type="checkbox"
            checked={draft.prompt_enabled !== false}
            onChange={(e) => patch('prompt_enabled', e.target.checked)}
          />
          启用 Prompt
        </label>
        <label className="block">
          <span className="sf-label">System</span>
          <textarea
            className={textareaCls}
            value={draft.system_prompt || ''}
            onChange={(e) => patch('system_prompt', e.target.value)}
            spellCheck={false}
          />
        </label>
        <label className="block">
          <span className="sf-label">User 模板</span>
          <textarea
            className={textareaCls}
            value={draft.user_prompt_tpl || ''}
            onChange={(e) => patch('user_prompt_tpl', e.target.value)}
            spellCheck={false}
          />
        </label>
        <label className="block">
          <span className="sf-label">约束 constraints</span>
          <textarea
            className={cn(textareaCls, 'min-h-[64px]')}
            value={draft.constraints || ''}
            onChange={(e) => patch('constraints', e.target.value)}
            spellCheck={false}
          />
        </label>
      </AdminInspectorSection>

      <AdminInspectorSection title="Tier1 分区">
        <Tier1SectionPicker
          catalog={tier1Catalog}
          selected={draft.tier1_sections || []}
          onChange={(sections) => patch('tier1_sections', sections)}
        />
      </AdminInspectorSection>

      <AdminInspectorSection title="Agent 技能（只读）">
        <p className="text-xs text-navy-400 mb-3 leading-relaxed">
          流程编排负责选用 Agent 并排顺序；技能清单在{' '}
          <Link to="/admin/agent?tab=registry" className="text-gold-400 hover:text-gold-300">
            Agent 中心 · 注册表
          </Link>{' '}
          维护。
        </p>
        <SubSkillCardGrid skills={draft.sub_skills || []} readonly />
      </AdminInspectorSection>

      <AdminInspectorSection title="模型路由">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block">
            <span className="sf-label">Max Tokens</span>
            <input
              type="number"
              min={256}
              step={256}
              className={fieldNarrow}
              value={draft.max_tokens ?? draft.route_max_tokens ?? ''}
              onChange={(e) =>
                patch('max_tokens', e.target.value === '' ? null : Number(e.target.value))
              }
            />
          </label>
          <label className="block sm:col-span-1">
            <span className="sf-label">使用大模型</span>
            <select
              className={fieldMedium}
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
        </div>
      </AdminInspectorSection>

      <div className="flex items-center justify-between gap-3 pt-3 border-t border-white/5 sticky bottom-0 bg-slate-950/90 py-2 backdrop-blur">
        <span className={cn('text-xs', dirty ? 'text-gold-300' : 'text-navy-400')}>
          {dirty ? '有未保存修改' : '已同步'}
        </span>
        <button
          type="button"
          disabled={!dirty || saving}
          onClick={() => onSave?.(draft)}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-40"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '保存步骤'}
        </button>
      </div>
    </div>
  )
}

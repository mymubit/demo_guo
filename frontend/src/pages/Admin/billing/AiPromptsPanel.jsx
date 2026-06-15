import { Link } from 'react-router-dom'
import { Save } from 'lucide-react'
import { toast } from 'sonner'
import { admin } from '@/services/api'
import { formatActionKeyTitle } from '@/utils/adminAgentLabels'
import { AdminBadge, AdminEmpty } from '@/components/admin/AdminUI'
import AdminMasterDetail, { AdminMasterDetailListButton } from '@/components/admin/AdminMasterDetail'
import { useBilling } from './BillingContext.jsx'
import { COIN_PRICING_NOTE } from '@/utils/adminEconomics'

export default function AiPromptsPanel() {
  const {
    aiPrompts, promptDirty, pricingDirty, pricingByActionKey, pricing, currencyName, savingId,
    selectedPromptKey, setSelectedPromptKey, llmProviders, patchAiPrompt, saveAiPromptRow,
    patchPricingRow, loadAll, setSavingId, extraAuxPricing, selectedExtraPricingId,
    setSelectedExtraPricingId, agentCatalog, savePricingRow,
  } = useBilling()
  return (
<div className="space-y-6">
              <div className="glass-card rounded-2xl p-5 border border-blue-500/15 bg-blue-500/5">
                <p className="text-sm text-navy-200 leading-relaxed">
                  <span className="text-white font-medium">填表 AI + 辅助动作</span>
                  ——创作页填表按钮在此配提示词、单次扣费与模型；整链提交等其它 action 扣费见下方「其他辅助扣费」。正式世界观在
                  <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
                    WorldAgent（步骤 2）
                  </Link>
                  ，与填表辅助不是同一能力。
                  <span className="block mt-2 text-xs text-navy-400">{COIN_PRICING_NOTE}</span>
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-end gap-3">
                <button
                  type="button"
                  className="px-4 py-2 rounded-xl bg-navy-800 text-gold-400 text-sm border border-gold-500/30"
                  disabled={savingId === 'seed-prompts'}
                  onClick={async () => {
                    setSavingId('seed-prompts')
                    try {
                      await admin.seedAiFieldPrompts()
                      toast.success('已写入默认提示词')
                      await loadAll()
                    } catch (err) {
                      toast.error(err.message || '写入失败')
                    } finally {
                      setSavingId(null)
                    }
                  }}
                >
                  导入默认值
                </button>
                <button
                  type="button"
                  className="px-4 py-2 rounded-xl bg-navy-800 text-gold-400 text-sm border border-gold-500/30"
                  disabled={savingId === 'create-pricing'}
                  onClick={async () => {
                    const action_key = window.prompt('动作键 action_key', 'ai.generate.custom')
                    if (!action_key) return
                    setSavingId('create-pricing')
                    try {
                      await admin.savePricing({
                        action_key,
                        display_name: action_key,
                        coin_cost: 10,
                        is_active: true,
                        member_only: false,
                      })
                      toast.success('定价已创建')
                      loadAll()
                    } catch (err) {
                      toast.error(err.message || '创建失败')
                    } finally {
                      setSavingId(null)
                    }
                  }}
                >
                  {savingId === 'create-pricing' ? '创建中…' : '新增定价'}
                </button>
              </div>

              {aiPrompts.length === 0 ? (
                <AdminEmpty title="暂无提示词" description="点击「导入默认值」或执行 init_billing_data" />
              ) : (
                <AdminMasterDetail
                  listTitle="填表 AI"
                  listHint="提示词 + 扣费 + 模型"
                  detailTitle="编辑辅助能力"
                  items={aiPrompts}
                  selectedId={selectedPromptKey}
                  onSelect={setSelectedPromptKey}
                  getId={(row) => row.action_key}
                  renderListItem={(row, { active, onSelect }) => {
                    const priceRow = pricingByActionKey[row.action_key]
                    return (
                      <AdminMasterDetailListButton
                        key={row.action_key}
                        active={active}
                        onClick={onSelect}
                        title={row.display_name || row.action_key}
                        subtitle={row.action_key}
                        meta={
                          priceRow
                            ? `${priceRow.coin_cost} ${currencyName}`
                            : undefined
                        }
                        dirty={
                          promptDirty.has(row.action_key) ||
                          (priceRow && pricingDirty.has(priceRow.id))
                        }
                      />
                    )
                  }}
                  renderDetail={(row) => {
                    const priceRow = pricingByActionKey[row.action_key]
                    return (
                    <div className="space-y-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h3 className="text-lg font-semibold text-white">
                            {formatActionKeyTitle(row.action_key, agentCatalog, row.display_name || row.action_key)}
                          </h3>
                          <p className="text-xs font-mono text-navy-400 mt-1">{row.action_key}</p>
                        </div>
                        <AdminBadge tone={row.source === 'db' ? 'success' : 'default'}>
                          {row.source === 'db' ? '已入库' : '代码默认'}
                        </AdminBadge>
                      </div>
                      <label className="block text-sm text-navy-300">
                        中文展示名
                        <input
                          className="mt-1 w-full max-w-md rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm"
                          value={row.display_name || ''}
                          onChange={(e) => patchAiPrompt(row.action_key, { display_name: e.target.value })}
                          placeholder="如：目标受众"
                        />
                        <span className="text-xs text-navy-500 mt-1 block">面向运营与 C 端展示；下方动作键为系统标识，不可修改。</span>
                      </label>
                      <label className="block text-sm text-navy-300">
                        使用大模型
                        <select
                          className="mt-1 w-full max-w-md rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm"
                          value={row.llm_provider_id || ''}
                          onChange={(e) =>
                            patchAiPrompt(row.action_key, {
                              llm_provider_id: e.target.value || null,
                            })
                          }
                        >
                          <option value="">跟随全局激活模型</option>
                          {llmProviders.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                              {p.is_active ? '（当前全局）' : ''}
                            </option>
                          ))}
                        </select>
                      </label>
                      {priceRow && (
                        <label className="block text-sm text-navy-300">
                          单次扣费（{currencyName}）
                          <input
                            type="number"
                            min={0}
                            className="mt-1 w-full max-w-xs rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm"
                            value={priceRow.coin_cost}
                            onChange={(e) =>
                              patchPricingRow(priceRow.id, { coin_cost: e.target.value })
                            }
                          />
                        </label>
                      )}
                      <div className="flex flex-wrap gap-6 text-sm text-navy-200">
                        <label className="inline-flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={!!row.response_json}
                            onChange={(e) => patchAiPrompt(row.action_key, { response_json: e.target.checked })}
                          />
                          返回 JSON
                        </label>
                        <label className="inline-flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={!!row.is_active}
                            onChange={(e) => patchAiPrompt(row.action_key, { is_active: e.target.checked })}
                          />
                          启用
                        </label>
                      </div>
                      <label className="block text-xs text-navy-400">
                        System 提示词
                        <textarea
                          className="mt-1 w-full h-32 rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm font-mono resize-y"
                          value={row.system_prompt || ''}
                          onChange={(e) => patchAiPrompt(row.action_key, { system_prompt: e.target.value })}
                        />
                      </label>
                      <label className="block text-xs text-navy-400">
                        User 模板
                        <textarea
                          className="mt-1 w-full h-28 rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm font-mono resize-y"
                          value={row.user_prompt_tpl || ''}
                          onChange={(e) => patchAiPrompt(row.action_key, { user_prompt_tpl: e.target.value })}
                        />
                      </label>
                      <label className="block text-xs text-navy-400">
                        备用 System（JSON 失败降级，可选）
                        <textarea
                          className="mt-1 w-full h-20 rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm font-mono resize-y"
                          value={row.system_prompt_fallback || ''}
                          onChange={(e) =>
                            patchAiPrompt(row.action_key, { system_prompt_fallback: e.target.value })
                          }
                        />
                      </label>
                      <div className="flex items-center justify-between gap-3 pt-1 border-t border-navy-700/40">
                        <span className="text-xs text-navy-500">
                          {promptDirty.has(row.action_key) ||
                          (priceRow && pricingDirty.has(priceRow.id))
                            ? '有未保存修改'
                            : '已同步'}
                        </span>
                        <button
                          type="button"
                          disabled={savingId === `prompt-${row.action_key}`}
                          onClick={() => saveAiPromptRow(aiPrompts.find((i) => i.action_key === row.action_key))}
                          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
                        >
                          <Save className="w-4 h-4" />
                          {savingId === `prompt-${row.action_key}` ? '保存中…' : '保存'}
                        </button>
                      </div>
                    </div>
                    )
                  }}
                />
              )}

              {extraAuxPricing.length > 0 && (
                <details open className="glass-card rounded-2xl p-4">
                  <summary className="cursor-pointer text-white font-medium select-none mb-4">
                    其他辅助扣费
                    <span className="text-xs text-navy-500 font-normal ml-2">整链提交等；主链步骤币价在「主链 Agent」</span>
                  </summary>
                  <AdminMasterDetail
                    listTitle="动作定价"
                    listHint="非填表 AI 的辅助 action"
                    detailTitle="编辑扣费"
                    items={extraAuxPricing}
                    selectedId={selectedExtraPricingId}
                    onSelect={setSelectedExtraPricingId}
                    getId={(row) => row.id}
                    renderListItem={(row, { active, onSelect }) => (
                      <AdminMasterDetailListButton
                        key={row.id}
                        active={active}
                        onClick={onSelect}
                        title={formatActionKeyTitle(row.action_key, agentCatalog, row.display_name || row.action_key)}
                        subtitle={row.action_key}
                        meta={`${row.coin_cost} ${currencyName}`}
                        dirty={pricingDirty.has(row.id)}
                      />
                    )}
                    renderDetail={(row) => (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-white">
                          {formatActionKeyTitle(row.action_key, agentCatalog, row.display_name || row.action_key)}
                        </h3>
                        <p className="text-xs font-mono text-navy-400">{row.action_key}</p>
                        <label className="block text-sm text-navy-300">
                          展示名
                          <input
                            className="mt-1 w-full max-w-md rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm"
                            value={row.display_name || ''}
                            onChange={(e) => patchPricingRow(row.id, { display_name: e.target.value })}
                          />
                        </label>
                        <label className="block text-sm text-navy-300">
                          扣费（{currencyName}）
                          <input
                            type="number"
                            min={0}
                            className="mt-1 w-full max-w-xs rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white text-sm"
                            value={row.coin_cost}
                            onChange={(e) => patchPricingRow(row.id, { coin_cost: e.target.value })}
                          />
                        </label>
                        <label className="inline-flex items-center gap-2 text-sm text-navy-200">
                          <input
                            type="checkbox"
                            checked={!!row.is_active}
                            onChange={(e) => patchPricingRow(row.id, { is_active: e.target.checked })}
                          />
                          启用
                        </label>
                        <label className="inline-flex items-center gap-2 text-sm text-navy-200">
                          <input
                            type="checkbox"
                            checked={!!row.member_only}
                            onChange={(e) => patchPricingRow(row.id, { member_only: e.target.checked })}
                          />
                          仅会员
                        </label>
                        <div className="flex justify-end pt-2 border-t border-navy-700/40">
                          <button
                            type="button"
                            disabled={savingId === `pricing-${row.id}`}
                            onClick={() => savePricingRow(pricing.find((item) => item.id === row.id))}
                            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
                          >
                            <Save className="w-4 h-4" />
                            {savingId === `pricing-${row.id}` ? '保存中…' : '保存'}
                          </button>
                        </div>
                      </div>
                    )}
                  />
                </details>
              )}
            </div>
  )
}

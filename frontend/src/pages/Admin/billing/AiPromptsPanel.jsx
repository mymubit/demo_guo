import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Save } from 'lucide-react'
import { toast } from 'sonner'
import { admin } from '@/services/api'
import { formatActionKeyTitle } from '@/utils/adminAgentLabels'
import { AdminEmpty } from '@/components/admin/AdminUI'
import AdminAgentPromptEditor from '@/components/admin/AdminAgentPromptEditor'
import AdminMasterDetail, { AdminMasterDetailListButton } from '@/components/admin/AdminMasterDetail'
import { useBilling } from './BillingContext.jsx'
import { COIN_PRICING_NOTE } from '@/utils/adminEconomics'

export default function AiPromptsPanel() {
  const [searchParams] = useSearchParams()
  const {
    aiPrompts,
    promptDirty,
    pricingDirty,
    pricingByActionKey,
    pricing,
    currencyName,
    savingId,
    selectedPromptKey,
    setSelectedPromptKey,
    llmProviders,
    patchAiPrompt,
    saveAiPromptRow,
    patchPricingRow,
    loadAll,
    setSavingId,
    extraAuxPricing,
    selectedExtraPricingId,
    setSelectedExtraPricingId,
    agentCatalog,
    savePricingRow,
  } = useBilling()

  useEffect(() => {
    const action = searchParams.get('action')
    if (action) setSelectedPromptKey(action)
  }, [searchParams, setSelectedPromptKey])

  return (
    <div className="space-y-5">
      <div className="sf-console-panel px-4 py-3.5">
        <p className="text-sm text-navy-300 leading-relaxed">
          <span className="text-white font-medium">填表 Agent</span>
          服务创作页字段按钮（目标受众、核心创意等），与流水线 Agent 同属 Agent 体系。
        </p>
        <p className="text-xs text-navy-400 mt-2">{COIN_PRICING_NOTE}</p>
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          className="px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 hover:bg-white/[0.06]"
          disabled={savingId === 'seed-prompts'}
          onClick={async () => {
            setSavingId('seed-prompts')
            try {
              await admin.seedAiFieldPrompts()
              toast.success('已写入默认填表 Agent')
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
      </div>

      {aiPrompts.length === 0 ? (
        <AdminEmpty title="暂无填表 Agent" description="点击「导入默认值」初始化" />
      ) : (
        <AdminMasterDetail
          listTitle="填表 Agent"
          listHint="创作页字段级 Agent"
          detailTitle="Agent 配置"
          items={aiPrompts}
          selectedId={selectedPromptKey}
          onSelect={setSelectedPromptKey}
          getId={(row) => row.action_key}
          sidebarWidthClass="lg:grid-cols-[240px_minmax(0,1fr)]"
          minHeightClass="min-h-[480px]"
          renderListItem={(row, { active, onSelect }) => {
            const priceRow = pricingByActionKey[row.action_key]
            return (
              <AdminMasterDetailListButton
                key={row.action_key}
                active={active}
                onClick={onSelect}
                title={row.display_name || row.action_key}
                subtitle={row.action_key}
                meta={priceRow ? `${priceRow.coin_cost} ${currencyName}` : undefined}
                badges={row.is_active === false ? ['停用'] : []}
                dirty={
                  promptDirty.has(row.action_key) ||
                  (priceRow && pricingDirty.has(priceRow.id))
                }
              />
            )
          }}
          renderDetail={(row) => {
            const priceRow = pricingByActionKey[row.action_key]
            const dirty =
              promptDirty.has(row.action_key) ||
              (priceRow && pricingDirty.has(priceRow.id))
            return (
              <AdminAgentPromptEditor
                kind="form"
                title={formatActionKeyTitle(
                  row.action_key,
                  agentCatalog,
                  row.display_name || row.action_key,
                )}
                subtitle={row.action_key}
                sourceBadge={row.source}
                displayName={row.display_name || ''}
                onDisplayNameChange={(value) => patchAiPrompt(row.action_key, { display_name: value })}
                displayNameHint="动作键为系统标识，不可修改"
                llmProviders={llmProviders}
                llmProviderId={row.llm_provider_id}
                onLlmProviderChange={(value) =>
                  patchAiPrompt(row.action_key, { llm_provider_id: value })
                }
                coinCost={priceRow?.coin_cost}
                onCoinCostChange={
                  priceRow
                    ? (value) => patchPricingRow(priceRow.id, { coin_cost: value })
                    : undefined
                }
                currencyName={currencyName}
                responseJson={row.response_json}
                onResponseJsonChange={(value) =>
                  patchAiPrompt(row.action_key, { response_json: value })
                }
                isActive={row.is_active}
                onIsActiveChange={(value) => patchAiPrompt(row.action_key, { is_active: value })}
                systemPrompt={row.system_prompt}
                onSystemPromptChange={(value) =>
                  patchAiPrompt(row.action_key, { system_prompt: value })
                }
                userPromptTpl={row.user_prompt_tpl}
                onUserPromptTplChange={(value) =>
                  patchAiPrompt(row.action_key, { user_prompt_tpl: value })
                }
                systemPromptFallback={row.system_prompt_fallback}
                onSystemPromptFallbackChange={(value) =>
                  patchAiPrompt(row.action_key, { system_prompt_fallback: value })
                }
                dirty={dirty}
                saving={savingId === `prompt-${row.action_key}`}
                onSave={() =>
                  saveAiPromptRow(aiPrompts.find((item) => item.action_key === row.action_key))
                }
              />
            )
          }}
        />
      )}

      {extraAuxPricing.length > 0 ? (
        <details className="sf-console-panel group">
          <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-navy-200">
            其他辅助扣费
            <span className="text-xs text-navy-400 font-normal ml-2">整链提交等</span>
          </summary>
          <div className="px-4 pb-4 border-t border-white/5 pt-3">
            <AdminMasterDetail
              listTitle="动作定价"
              listHint="非填表 Agent"
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
                  title={formatActionKeyTitle(
                    row.action_key,
                    agentCatalog,
                    row.display_name || row.action_key,
                  )}
                  subtitle={row.action_key}
                  meta={`${row.coin_cost} ${currencyName}`}
                  dirty={pricingDirty.has(row.id)}
                />
              )}
              renderDetail={(row) => (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">
                    {formatActionKeyTitle(
                      row.action_key,
                      agentCatalog,
                      row.display_name || row.action_key,
                    )}
                  </h3>
                  <p className="text-xs font-mono text-navy-300">{row.action_key}</p>
                  <label className="block text-sm text-navy-300">
                    展示名
                    <input
                      className="mt-1 w-full max-w-md rounded-xl bg-slate-900 border border-white/5 px-3 py-2 text-white text-sm"
                      value={row.display_name || ''}
                      onChange={(e) => patchPricingRow(row.id, { display_name: e.target.value })}
                    />
                  </label>
                  <label className="block text-sm text-navy-300">
                    扣费（{currencyName}）
                    <input
                      type="number"
                      min={0}
                      className="mt-1 w-full max-w-xs rounded-xl bg-slate-900 border border-white/5 px-3 py-2 text-white text-sm"
                      value={row.coin_cost}
                      onChange={(e) => patchPricingRow(row.id, { coin_cost: e.target.value })}
                    />
                  </label>
                  <div className="flex flex-wrap gap-4 text-sm text-navy-200">
                    <label className="inline-flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!row.is_active}
                        onChange={(e) => patchPricingRow(row.id, { is_active: e.target.checked })}
                      />
                      启用
                    </label>
                    <label className="inline-flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={!!row.member_only}
                        onChange={(e) => patchPricingRow(row.id, { member_only: e.target.checked })}
                      />
                      仅会员
                    </label>
                  </div>
                  <div className="flex justify-end pt-2 border-t border-white/5">
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
          </div>
        </details>
      ) : null}
    </div>
  )
}

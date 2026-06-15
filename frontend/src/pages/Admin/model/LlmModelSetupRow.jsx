import { ChevronDown, Save } from 'lucide-react'
import {
  formatPricingPairPerThousand,
  perMillionToPerThousand,
} from '@/utils/llmPricingUnits'
import { hasSavedCatalogPricing } from '@/hooks/useCatalogPricing'

export default function LlmModelSetupRow({
  preset,
  catalogRow,
  pricingDraft = {},
  pricingSaving = false,
  onPatchPricing,
  onSavePricing,
  onConnect,
}) {
  const row = catalogRow || preset
  const savedHint = formatPricingPairPerThousand(
    row.input_price_per_million,
    row.output_price_per_million,
  )
  const dirty =
    pricingDraft.input_price_per_thousand !==
      (row.input_price_per_million != null && row.input_price_per_million !== ''
        ? perMillionToPerThousand(row.input_price_per_million)
        : '') ||
    pricingDraft.output_price_per_thousand !==
      (row.output_price_per_million != null && row.output_price_per_million !== ''
        ? perMillionToPerThousand(row.output_price_per_million)
        : '')

  return (
    <details
      className="rounded-lg border border-navy-700/35 bg-navy-900/30 group"
      defaultOpen={!preset.configured || !hasSavedCatalogPricing(row)}
    >
      <summary className="cursor-pointer list-none px-3 py-2.5 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm text-white font-medium">{preset.name}</p>
          <p className="text-[10px] text-navy-500 font-mono truncate">{preset.model_name}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0 justify-end">
          <span className={`text-[10px] ${preset.configured ? 'text-green-400' : 'text-navy-500'}`}>
            {preset.configured ? '已接入' : '未接入'}
          </span>
          <span className={`text-xs ${savedHint ? 'text-navy-400' : 'text-amber-300'}`}>
            {savedHint || '未设单价'}
          </span>
          {dirty ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gold-500/15 text-gold-300">
              未保存
            </span>
          ) : null}
          <ChevronDown className="w-3.5 h-3.5 text-navy-500 transition group-open:rotate-180" />
        </div>
      </summary>
      <div className="px-3 pb-3 pt-1 border-t border-navy-700/30 space-y-3">
        <p className="text-[10px] text-navy-500">
          Dashboard「大模型成本」核算用，与「主链 Agent」创作币扣费无关。单价与控制台「元/千 Token」一致。
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">输入 元/千 Token</span>
            <input
              type="number"
              step="0.000001"
              min="0"
              value={pricingDraft.input_price_per_thousand ?? ''}
              onChange={(e) => onPatchPricing(row.id, 'input_price_per_thousand', e.target.value)}
              placeholder="如 0.012"
              className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">输出 元/千 Token</span>
            <input
              type="number"
              step="0.000001"
              min="0"
              value={pricingDraft.output_price_per_thousand ?? ''}
              onChange={(e) => onPatchPricing(row.id, 'output_price_per_thousand', e.target.value)}
              placeholder="如 0.024"
              className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm"
            />
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={pricingSaving}
            onClick={() => onSavePricing(row)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs bg-gold-500/10 text-gold-300 border border-gold-500/25 hover:bg-gold-500/20 disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {pricingSaving ? '保存中…' : '保存单价'}
          </button>
          <button
            type="button"
            onClick={onConnect}
            className={`px-3 py-2 rounded-lg text-xs border transition ${
              preset.configured
                ? 'border-green-500/30 text-green-300 hover:bg-green-500/10'
                : 'border-gold-500/30 text-gold-300 hover:bg-gold-500/10'
            }`}
          >
            {preset.configured ? '编辑 model ID' : '接入 model ID'}
          </button>
        </div>
      </div>
    </details>
  )
}

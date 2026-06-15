import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { admin } from '@/services/api'
import { useAdminSelection } from '@/components/admin/AdminMasterDetail'
import { syncChargeFromDiscount } from '@/utils/adminEconomics'
import { groupPricing } from '@/utils/billingPricing'

export function useBillingAdmin(forcedTab) {
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)
  const [settings, setSettings] = useState({})
  const [pricing, setPricing] = useState([])
  const [rechargePackages, setRechargePackages] = useState([])
  const [aiPrompts, setAiPrompts] = useState([])
  const [promptDirty, setPromptDirty] = useState(() => new Set())
  const [pricingDirty, setPricingDirty] = useState(() => new Set())
  const [rechargeDirty, setRechargeDirty] = useState(() => new Set())
  const [llmProviders, setLlmProviders] = useState([])
  const [agentCatalog, setAgentCatalog] = useState(null)
  const [selectedPromptKey, setSelectedPromptKey] = useAdminSelection(
    aiPrompts,
    (row) => row.action_key
  )
  const pricingGroups = useMemo(() => groupPricing(pricing), [pricing])
  const flatPricing = useMemo(
    () =>
      pricingGroups
        .flatMap((group) =>
          group.items.map((item) => ({ ...item, groupLabel: group.label }))
        )
        .filter((item) => !item.action_key?.startsWith('pipeline.node.')),
    [pricingGroups]
  )
  const pricingByActionKey = useMemo(() => {
    const map = {}
    pricing.forEach((row) => {
      if (row.action_key) map[row.action_key] = row
    })
    return map
  }, [pricing])
  const extraAuxPricing = useMemo(
    () => flatPricing.filter((row) => !row.action_key?.startsWith('ai.generate.')),
    [flatPricing]
  )
  const [selectedExtraPricingId, setSelectedExtraPricingId] = useAdminSelection(
    extraAuxPricing,
    (row) => row.id
  )
  const [selectedRechargeId, setSelectedRechargeId] = useAdminSelection(
    rechargePackages,
    (row) => row.id
  )

  async function loadAll() {
    setLoading(true)
    try {
      if (forcedTab === 'ai-prompts') {
        const [prompts, p, llmRes, s, catalog] = await Promise.all([
          admin.listAiFieldPrompts(),
          admin.listPricing(),
          admin.getLlmConfig(),
          admin.getBillingSettings(),
          admin.agentCatalog().catch(() => null),
        ])
        setAiPrompts(Array.isArray(prompts) ? prompts : [])
        setPricing(Array.isArray(p) ? p : [])
        setLlmProviders(Array.isArray(llmRes?.providers) ? llmRes.providers.filter((x) => x.is_enabled) : [])
        setSettings(s ?? {})
        setAgentCatalog(catalog)
        return
      }

      if (forcedTab === 'commerce') {
        const [s, r] = await Promise.all([
          admin.getBillingSettings(),
          admin.listRechargePackages(),
        ])
        setSettings(s ?? {})
        setRechargePackages(Array.isArray(r) ? r : [])
      }
    } catch (err) {
      toast.error(err.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [forcedTab])

  function patchAiPrompt(actionKey, patch) {
    setAiPrompts((list) =>
      list.map((item) => (item.action_key === actionKey ? { ...item, ...patch } : item))
    )
    setPromptDirty((prev) => new Set(prev).add(actionKey))
  }

  function patchPricingRow(id, patch) {
    setPricing((list) =>
      list.map((item) => (item.id === id ? { ...item, ...patch } : item))
    )
    setPricingDirty((prev) => new Set(prev).add(id))
  }

  function patchRechargeRow(id, patch) {
    setRechargePackages((list) =>
      list.map((item) => {
        if (item.id !== id) return item
        const merged = { ...item, ...patch }
        if ('original_price_yuan' in patch || 'discount_percent' in patch) {
          merged.price_yuan = syncChargeFromDiscount({
            original: merged.original_price_yuan,
            discountPercent: merged.discount_percent,
            manualPrice: merged.price_yuan,
          })
        }
        return merged
      })
    )
    setRechargeDirty((prev) => new Set(prev).add(id))
  }

  async function saveSettings() {
    setSavingId('settings')
    try {
      await admin.updateBillingSettings(settings)
      toast.success('站点币种设置已保存')
    } catch (err) {
      toast.error(err.message || '保存失败')
    } finally {
      setSavingId(null)
    }
  }

  async function savePricingRow(row) {
    setSavingId(`pricing-${row.id}`)
    try {
      await admin.updatePricing(row.id, {
        display_name: row.display_name,
        coin_cost: Number(row.coin_cost),
        is_active: row.is_active,
        member_only: !!row.member_only,
      })
      toast.success('定价已更新')
      setPricingDirty((prev) => {
        const next = new Set(prev)
        next.delete(row.id)
        return next
      })
    } catch (err) {
      toast.error(err.message || '更新失败')
    } finally {
      setSavingId(null)
    }
  }

  async function saveAiPromptRow(row) {
    setSavingId(`prompt-${row.action_key}`)
    try {
      if (row.id) {
        await admin.updateAiFieldPrompt(row.id, {
          display_name: row.display_name,
          system_prompt: row.system_prompt,
          user_prompt_tpl: row.user_prompt_tpl,
          system_prompt_fallback: row.system_prompt_fallback,
          response_json: !!row.response_json,
          is_active: !!row.is_active,
          llm_provider_id: row.llm_provider_id || null,
        })
      } else {
        await admin.saveAiFieldPrompt({
          action_key: row.action_key,
          display_name: row.display_name,
          system_prompt: row.system_prompt,
          user_prompt_tpl: row.user_prompt_tpl,
          system_prompt_fallback: row.system_prompt_fallback,
          response_json: !!row.response_json,
          is_active: !!row.is_active,
          llm_provider_id: row.llm_provider_id || null,
        })
      }
      const priceRow = pricingByActionKey[row.action_key]
      if (priceRow && pricingDirty.has(priceRow.id)) {
        await admin.updatePricing(priceRow.id, {
          display_name: priceRow.display_name,
          coin_cost: Number(priceRow.coin_cost),
          is_active: priceRow.is_active,
          member_only: !!priceRow.member_only,
        })
        setPricingDirty((prev) => {
          const next = new Set(prev)
          next.delete(priceRow.id)
          return next
        })
      }
      toast.success('已保存')
      setPromptDirty((prev) => {
        const next = new Set(prev)
        next.delete(row.action_key)
        return next
      })
      await loadAll()
    } catch (err) {
      toast.error(err.message || '保存失败')
    } finally {
      setSavingId(null)
    }
  }

  async function saveRechargeRow(row) {
    setSavingId(`recharge-${row.id}`)
    try {
      await admin.updateRechargePackage(row.id, {
        name: row.name,
        price_yuan: row.price_yuan,
        original_price_yuan: row.original_price_yuan || null,
        discount_percent: row.discount_percent ?? 100,
        base_coins: Number(row.base_coins),
        bonus_coins: Number(row.bonus_coins),
        is_active: row.is_active,
        sort_order: Number(row.sort_order) || 0,
      })
      toast.success('档位已更新')
      setRechargeDirty((prev) => {
        const next = new Set(prev)
        next.delete(row.id)
        return next
      })
      await loadAll()
    } catch (err) {
      toast.error(err.message || '更新失败')
    } finally {
      setSavingId(null)
    }
  }

  async function createRechargePackageRow() {
    setSavingId('recharge-new')
    try {
      await admin.createRechargePackage({
        name: `新档位 ${rechargePackages.length + 1}`,
        price_yuan: '9.9',
        original_price_yuan: null,
        discount_percent: 100,
        base_coins: 100,
        bonus_coins: 0,
        is_active: false,
        sort_order: rechargePackages.length + 1,
      })
      toast.success('已创建充值档位')
      await loadAll()
    } catch (err) {
      toast.error(err.message || '创建失败')
    } finally {
      setSavingId(null)
    }
  }

  async function deleteRechargePackageRow(id) {
    if (!window.confirm('确定删除该充值档位？')) return
    setSavingId(`recharge-del-${id}`)
    try {
      await admin.deleteRechargePackage(id)
      toast.success('已删除')
      await loadAll()
    } catch (err) {
      toast.error(err.message || '删除失败')
    } finally {
      setSavingId(null)
    }
  }

  const currencyName = settings.currency_name || '创作币'

  return {
    forcedTab,
    loading,
    savingId,
    settings,
    setSettings,
    pricing,
    rechargePackages,
    aiPrompts,
    promptDirty,
    pricingDirty,
    rechargeDirty,
    llmProviders,
    agentCatalog,
    selectedPromptKey,
    setSelectedPromptKey,
    selectedExtraPricingId,
    setSelectedExtraPricingId,
    selectedRechargeId,
    setSelectedRechargeId,
    pricingByActionKey,
    extraAuxPricing,
    currencyName,
    loadAll,
    patchAiPrompt,
    patchPricingRow,
    patchRechargeRow,
    saveSettings,
    savePricingRow,
    saveAiPromptRow,
    saveRechargeRow,
    createRechargePackageRow,
    deleteRechargePackageRow,
    setSavingId,
  }
}

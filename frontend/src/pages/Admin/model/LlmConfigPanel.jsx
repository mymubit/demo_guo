import { motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ChevronDown,
  KeyRound,
  Plus,
  Save,
  SlidersHorizontal,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { admin } from '@/services/api'
import { LLM_PRICING_NOTE } from '@/utils/adminEconomics'
import {
  EMPTY_LLM_PROVIDER,
  inferVolcanoKeyType,
  volcanoBaseUrlForKeyType,
  VOLCANO_CODING_URL,
  VOLCANO_PAYG_URL,
} from '@/constants/adminShared'
import {
  formatAdminError,
} from '@/hooks/useAdminPanelMessage'
import LlmModelSetupRow from './LlmModelSetupRow'
import LlmVendorCredentialForm from './LlmVendorCredentialForm'
import { groupItemsByVendor, LlmVendorCollapse } from './LlmVendorCollapse'
import { hasSavedCatalogPricing, useCatalogPricing } from '@/hooks/useCatalogPricing'
import {
  formatPricingPairPerThousand,
  LLM_RECOMMENDED_PRESET_KEYS,
} from '@/utils/llmPricingUnits'

function providerPricingHint(provider, catalog = []) {
  const label = formatPricingPairPerThousand(
    provider.catalog_input_price_per_million,
    provider.catalog_output_price_per_million,
  )
  if (label) return `Dashboard 成本核算 ${label}`

  const cat = catalog.find((c) => c.id === provider.catalog_id)
  const catLabel = formatPricingPairPerThousand(
    cat?.input_price_per_million,
    cat?.output_price_per_million,
  )
  if (catLabel) return `Dashboard 成本核算 ${catLabel}`

  if (!provider.catalog_id) {
    return '未关联目录模板，LLM 成本可能记为 ¥0'
  }
  return '目录未设 Token 单价'
}

function findVendorCredential(credentials, vendor) {
  return credentials.find((item) => item.vendor === vendor)
}

function LlmProviderFormFields({
  form,
  setForm,
  apiKeyTouched,
  setApiKeyTouched,
  apiKeySet,
  apiKeyUrl,
  minimal = false,
  vendorApiKeySet = false,
}) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const isVolcengine =
    form.vendor === 'volcengine' ||
    String(form.base_url || '').includes('volces.com') ||
    String(form.base_url || '').includes('volcengine')
  const volcanoKeyType = form.volcano_key_type || inferVolcanoKeyType(form.base_url) || 'payg'

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {!minimal ? (
        <label className="block md:col-span-2">
          <span className="text-xs text-navy-400 mb-1 block">展示名称</span>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="sf-control"
          />
        </label>
      ) : null}

      {vendorApiKeySet && minimal && isVolcengine ? (
        <p className="text-xs text-navy-400 md:col-span-2">
          按量付费 Chat API：model 填 <span className="font-mono text-navy-300">ep-xxx</span>{' '}
          （控制台 → 在线推理 → 推理接入点）。也可填 Model ID 并在 .env 配置 VOLCANO_EP_* 自动映射。
        </p>
      ) : null}

      {vendorApiKeySet && minimal && !isVolcengine ? (
        <p className="text-xs text-navy-400 md:col-span-2">
          使用上方厂商共用 API Key，此处只需填写模型 ID。
        </p>
      ) : null}

      {!vendorApiKeySet ? (
        <label className="block md:col-span-2">
          <span className="text-xs text-navy-400 flex items-center gap-1 mb-1">
            <KeyRound className="w-3.5 h-3.5" /> API Key
            {apiKeyUrl ? (
              <a href={apiKeyUrl} target="_blank" rel="noreferrer" className="text-gold-400 hover:underline ml-2">
                去控制台获取
              </a>
            ) : null}
          </span>
          <input
            type="password"
            autoComplete="off"
            value={form.api_key}
            placeholder={apiKeySet && !apiKeyTouched ? '已设置，修改请重新输入' : '粘贴 API Key'}
            onChange={(e) => {
              setApiKeyTouched(true)
              setForm({ ...form, api_key: e.target.value })
            }}
            className="sf-control font-mono"
          />
        </label>
      ) : null}

      {isVolcengine && !vendorApiKeySet ? (
        <label className="block md:col-span-2">
          <span className="text-xs text-navy-400 mb-1 block">火山 Key 类型</span>
          <select
            value={volcanoKeyType}
            onChange={(e) => {
              const keyType = e.target.value
              setForm({
                ...form,
                volcano_key_type: keyType,
                base_url: volcanoBaseUrlForKeyType(keyType),
              })
            }}
            className="sf-control"
          >
            <option value="payg">按量付费（推荐）— ep-xxx / Model ID</option>
            <option value="coding_plan">Coding Plan — 仅编程订阅 Key</option>
          </select>
        </label>
      ) : null}

      <label className="block md:col-span-2">
        <span className="text-xs text-navy-400 mb-1 block">模型 ID / 接入点</span>
        <input
          value={form.model_name}
          placeholder={isVolcengine ? '按量付费填 ep-xxxxxxxx（推理接入点 ID）' : 'gpt-4o-mini'}
          onChange={(e) => setForm({ ...form, model_name: e.target.value })}
          className="sf-control font-mono"
        />
      </label>

      {!minimal ? (
        <>
          <label className="block md:col-span-2">
            <span className="text-xs text-navy-400 mb-1 block">Base URL</span>
            <input
              value={form.base_url}
              readOnly={isVolcengine}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              className="sf-control font-mono read-only:opacity-80"
            />
          </label>
          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">Temperature</span>
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={form.temperature}
              onChange={(e) => setForm({ ...form, temperature: e.target.value })}
              className="sf-control"
            />
          </label>
          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">Max Tokens</span>
            <input
              type="number"
              min={256}
              max={32000}
              step={256}
              value={form.max_tokens}
              onChange={(e) => setForm({ ...form, max_tokens: e.target.value })}
              className="sf-control"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-navy-200 md:col-span-2">
            <input
              type="checkbox"
              checked={!!form.is_enabled}
              onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
            />
            启用此模型
          </label>
          <div className="md:col-span-2 overflow-hidden rounded-xl border border-white/10">
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="flex w-full items-center justify-between bg-slate-900/40 px-4 py-3 text-sm text-navy-200"
            >
              <span className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4" />
                更多参数
              </span>
              <ChevronDown className={`w-4 h-4 transition ${showAdvanced ? 'rotate-180' : ''}`} />
            </button>
            {showAdvanced ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border-t border-white/5">
                <label className="block">
                  <span className="text-xs text-navy-400 mb-1 block">上下文窗口-输入</span>
                  <input
                    type="number"
                    value={form.context_window_input ?? ''}
                    onChange={(e) => setForm({ ...form, context_window_input: e.target.value })}
                    className="sf-control"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-navy-400 mb-1 block">备注</span>
                  <input
                    value={form.remark || ''}
                    onChange={(e) => setForm({ ...form, remark: e.target.value })}
                    className="sf-control"
                  />
                </label>
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  )
}

export default function LlmConfigPanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [showAllPresets, setShowAllPresets] = useState(false)
  const [globalEnabled, setGlobalEnabled] = useState(false)
  const [providers, setProviders] = useState([])
  const [presets, setPresets] = useState([])
  const [vendors, setVendors] = useState([])
  const [catalog, setCatalog] = useState([])
  const [vendorCredentials, setVendorCredentials] = useState([])
  const [status, setStatus] = useState(null)
  const [routingPlan, setRoutingPlan] = useState(null)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState({ ...EMPTY_LLM_PROVIDER })
  const [apiKeyTouched, setApiKeyTouched] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [connectedProvidersOpen, setConnectedProvidersOpen] = useState(true)

  function notify(text, type = 'success') {
    const msg = formatAdminError(text, type)
    if (type === 'error') toast.error(msg)
    else toast.success(msg)
    onMessage(msg, type)
  }

  function findProvider(id) {
    return providers.find((p) => p.id === id)
  }

  async function load() {
    setLoading(true)
    try {
      const [data, plan] = await Promise.all([
        admin.getLlmConfig(),
        admin.getLlmRoutingPlan().catch(() => null),
      ])
      setGlobalEnabled(!!data?.global_enabled)
      setProviders(Array.isArray(data?.providers) ? data.providers : [])
      setPresets(Array.isArray(data?.presets) ? data.presets : [])
      setVendors(Array.isArray(data?.vendors) ? data.vendors : [])
      setCatalog(Array.isArray(data?.catalog) ? data.catalog : [])
      setVendorCredentials(Array.isArray(data?.vendor_credentials) ? data.vendor_credentials : [])
      setStatus(data?.status || null)
      setRoutingPlan(plan)
    } catch (err) {
      notify(err.message || '加载大模型配置失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const selectedProvider = editingId ? findProvider(editingId) : null
  const editorOpen = creating || !!selectedProvider

  const presetList = useMemo(() => {
    const all = presets.length ? presets : catalog
    if (showAllPresets) return all
    const recommended = all.filter((p) => LLM_RECOMMENDED_PRESET_KEYS.has(p.preset_key || p.key))
    return recommended.length ? recommended : all.slice(0, 4)
  }, [presets, catalog, showAllPresets])

  const providerGroups = useMemo(() => groupItemsByVendor(providers), [providers])
  const presetGroups = useMemo(() => groupItemsByVendor(presetList), [presetList])

  const activeFormVendor = useMemo(() => {
    if (form.vendor) return form.vendor
    if (selectedProvider?.vendor) return selectedProvider.vendor
    const cat = catalog.find((c) => c.id === form.catalog_id)
    return cat?.vendor || ''
  }, [form.vendor, form.catalog_id, selectedProvider, catalog])

  const activeVendorCredential = findVendorCredential(vendorCredentials, activeFormVendor)

  function loadProviderForm(p) {
    setForm({
      ...EMPTY_LLM_PROVIDER,
      catalog_id: p.catalog_id || '',
      name: p.name,
      api_key: p.api_key || '',
      base_url: p.base_url,
      model_name: p.model_name,
      volcano_key_type: p.volcano_key_type || inferVolcanoKeyType(p.base_url),
      vendor: p.vendor || '',
      temperature: p.temperature,
      max_tokens: p.max_tokens,
      is_enabled: p.is_enabled,
      remark: p.remark || '',
    })
    setApiKeyTouched(false)
  }

  function applyPreset(preset) {
    setCreating(true)
    setEditingId(null)
    setForm({
      ...EMPTY_LLM_PROVIDER,
      catalog_id: preset.id,
      name: preset.name,
      base_url: preset.vendor === 'volcengine' ? VOLCANO_PAYG_URL : preset.base_url,
      model_name: preset.model_name,
      volcano_key_type: preset.vendor === 'volcengine' ? 'payg' : '',
      vendor: preset.vendor || '',
      temperature: preset.temperature ?? 0.7,
      max_tokens: preset.max_tokens ?? 8192,
      remark: preset.remark || '',
    })
    setApiKeyTouched(false)
  }

  function handlePresetClick(preset) {
    const existing = providers.find(
      (p) => p.catalog_id === preset.id || (p.model_name === preset.model_name && p.base_url === preset.base_url),
    )
    if (existing) {
      setCreating(false)
      setEditingId(existing.id)
      loadProviderForm(existing)
      return
    }
    applyPreset(preset)
  }

  function closeEditor() {
    setCreating(false)
    setEditingId(null)
    setForm({ ...EMPTY_LLM_PROVIDER })
    setApiKeyTouched(false)
  }

  function buildPayload(extra = {}) {
    const payload = {
      name: form.name,
      catalog_id: form.catalog_id || undefined,
      base_url: form.base_url,
      model_name: form.model_name,
      volcano_key_type: form.volcano_key_type || undefined,
      temperature: Number(form.temperature),
      max_tokens: Number(form.max_tokens),
      is_enabled: form.is_enabled !== false,
      remark: form.remark || '',
      ...extra,
    }
    if (apiKeyTouched && form.api_key) payload.api_key = form.api_key
    return payload
  }

  async function refreshFromResponse(data) {
    setProviders(Array.isArray(data?.providers) ? data.providers : [])
    setPresets(Array.isArray(data?.presets) ? data.presets : [])
    setVendors(Array.isArray(data?.vendors) ? data.vendors : [])
    setCatalog(Array.isArray(data?.catalog) ? data.catalog : [])
    setVendorCredentials(Array.isArray(data?.vendor_credentials) ? data.vendor_credentials : [])
    setStatus(data?.status || null)
  }

  const pricing = useCatalogPricing(catalog, {
    onMessage: notify,
    onUpdated: refreshFromResponse,
  })

  async function toggleGlobal(enabled) {
    try {
      const data = await admin.updateLlmGlobalSettings({ enabled })
      setGlobalEnabled(!!data?.global_enabled)
      await refreshFromResponse(data)
      notify(enabled ? '已启用大语言模型' : '已关闭大语言模型')
    } catch (err) {
      notify(err.message || '更新失败', 'error')
    }
  }

  async function handleCreate() {
    setBusyId('create')
    try {
      const data = await admin.createLlmProvider(buildPayload({ set_active: providers.length === 0 }))
      await refreshFromResponse(data)
      closeEditor()
      notify('模型已保存')
    } catch (err) {
      notify(err.message || '保存失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleUpdate(id) {
    setBusyId(id)
    try {
      const data = await admin.updateLlmProvider(id, buildPayload())
      await refreshFromResponse(data)
      setApiKeyTouched(false)
      notify('已保存')
    } catch (err) {
      notify(err.message || '保存失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleActivate(id) {
    const target = findProvider(id)
    if (target && !target.vendor_api_key_set) {
      notify('请先在该厂商下保存共用 API Key', 'error')
      return
    }
    setBusyId(id)
    try {
      const data = await admin.activateLlmProvider(id)
      await refreshFromResponse(data)
      notify('已设为全局默认模型')
    } catch (err) {
      notify(err.message || '切换失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('确定删除此模型配置？')) return
    setBusyId(id)
    try {
      const data = await admin.deleteLlmProvider(id)
      await refreshFromResponse(data)
      if (editingId === id) closeEditor()
      notify('已删除')
    } catch (err) {
      notify(err.message || '删除失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleTest(id) {
    const target = id ? findProvider(id) : null
    if (target && !target.vendor_api_key_set) {
      notify('请先在该厂商下保存共用 API Key', 'error')
      return
    }
    const busyKey = id ? `test-${id}` : 'test-active'
    setBusyId(busyKey)
    try {
      const data = await admin.testLlmConfig(id ? { provider_id: id } : {})
      if (data?.providers) await refreshFromResponse(data)
      notify(data?.message || '连通测试成功')
    } catch (err) {
      notify(err.message || '测试失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleSyncPresets() {
    setBusyId('sync-presets')
    try {
      const data = await admin.syncLlmPresets()
      await refreshFromResponse(data)
      notify('目录已同步')
    } catch (err) {
      notify(err.message || '同步失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleEnvSetup() {
    if (!window.confirm('从 .env 读取火山/智谱 Key 并自动创建接入？')) return
    setBusyId('env-setup')
    try {
      const data = await admin.setupLlmFromEnv()
      setGlobalEnabled(!!data?.global_enabled)
      await refreshFromResponse(data)
      setRoutingPlan(data?.routing_plan || null)
      notify(`环境变量接入完成：${data?.provider_count ?? 0} 个模型`)
    } catch (err) {
      notify(err.message || '接入失败', 'error')
    } finally {
      setBusyId(null)
    }
  }

  if (loading) {
    return <div className="text-center py-16 text-navy-400">加载大模型配置…</div>
  }

  const ready = status?.ready
  const boundNodeCount = routingPlan
    ? Object.values(routingPlan.nodes || {}).filter((n) => n.provider_id).length
    : 0
  const totalNodes = routingPlan ? Object.keys(routingPlan.nodes || {}).length : 0

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="sf-console-panel px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-white cursor-pointer">
            <input
              type="checkbox"
              checked={globalEnabled}
              onChange={(e) => toggleGlobal(e.target.checked)}
              className="w-4 h-4"
            />
            启用 LLM
          </label>
          <span
            className={`text-xs px-2.5 py-1 rounded-full ${
              ready ? 'bg-green-500/15 text-green-400' : 'bg-amber-500/15 text-amber-300'
            }`}
          >
            {ready ? '可创作' : '未就绪'}
          </span>
          {status?.active_provider_name ? (
            <span className="text-xs text-navy-400">
              全局默认：<span className="text-purple-300">{status.active_provider_name}</span>
            </span>
          ) : null}
          {totalNodes ? (
            <span className="text-xs text-navy-400">
              Agent 路由已绑 {boundNodeCount}/{totalNodes}
            </span>
          ) : null}
        </div>
      </div>

      <div className="space-y-5">
          <p className="text-xs text-navy-400">
            {LLM_PRICING_NOTE}
          </p>

          {/* 已接入 */}
          {providers.length > 0 ? (
            <details
              className="rounded-xl border border-white/10 bg-slate-900/40 group"
              open={connectedProvidersOpen}
              onToggle={(event) => setConnectedProvidersOpen(event.currentTarget.open)}
            >
              <summary className="cursor-pointer list-none px-4 py-3 flex items-center justify-between gap-2">
                <span className="text-xs text-navy-400 font-medium">已接入（{providers.length}）</span>
                <ChevronDown className="w-4 h-4 text-navy-400 transition group-open:rotate-180" />
              </summary>
              <div className="px-3 pb-3 pt-1 space-y-2 border-t border-white/5">
                {providerGroups.map((group) => (
                  <LlmVendorCollapse
                    key={group.vendor}
                    label={group.label}
                    count={group.items.length}
                    defaultOpen={group.items.some((p) => p.is_active) || group.vendor === 'volcengine'}
                  >
                    <div className="flex flex-wrap gap-2">
                      {group.items.map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => {
                            setCreating(false)
                            setEditingId(p.id)
                            loadProviderForm(p)
                          }}
                          className={`text-left px-3 py-2 rounded-xl border text-sm transition ${
                            editingId === p.id && !creating
                              ? 'border-gold-500/40 bg-gold-500/10 text-gold-200'
                              : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20'
                          }`}
                        >
                          <span className="font-medium block">{p.name}</span>
                          <span className="text-[10px] text-navy-300 font-mono">{p.model_name}</span>
                          <span
                            className={`text-[10px] block mt-0.5 ${
                              p.catalog_id && p.catalog_input_price_per_million != null
                                ? 'text-navy-400'
                                : 'text-amber-400'
                            }`}
                          >
                            {providerPricingHint(p, catalog)}
                          </span>
                          {p.is_active ? (
                            <span className="text-[10px] text-gold-400 block mt-0.5">全局默认</span>
                          ) : null}
                        </button>
                      ))}
                    </div>
                  </LlmVendorCollapse>
                ))}
              </div>
            </details>
          ) : null}

          {/* 内联编辑器 */}
          {editorOpen ? (
            <div className="sf-console-panel p-5 border border-gold-500/25 space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h4 className="text-white font-semibold">
                    {creating ? `接入：${form.name || '新模型'}` : `编辑：${selectedProvider?.name}`}
                  </h4>
                  <p className="text-xs text-navy-400 mt-0.5">
                    {activeVendorCredential?.api_key_set
                      ? '只需填模型 ID，Key 使用厂商共用'
                      : '请先在该厂商区块保存共用 API Key'}
                  </p>
                  {creating && form.catalog_id ? (
                    <p className="text-xs text-navy-400 mt-1">
                      {providerPricingHint(
                        {
                          catalog_id: form.catalog_id,
                          catalog_input_price_per_million: catalog.find((c) => c.id === form.catalog_id)
                            ?.input_price_per_million,
                          catalog_output_price_per_million: catalog.find((c) => c.id === form.catalog_id)
                            ?.output_price_per_million,
                        },
                        catalog,
                      )}
                    </p>
                  ) : null}
                  {!creating && selectedProvider && !selectedProvider.catalog_id ? (
                    <p className="text-xs text-amber-400 mt-1">
                      此实例未关联目录模板，Dashboard 的 LLM 成本无法按 Token 单价核算。请删除后从模板重新接入。
                    </p>
                  ) : null}
                </div>
                <button type="button" onClick={closeEditor} className="text-xs text-navy-400 hover:text-white">
                  取消
                </button>
              </div>
              <LlmProviderFormFields
                form={form}
                setForm={setForm}
                apiKeyTouched={apiKeyTouched}
                setApiKeyTouched={setApiKeyTouched}
                apiKeySet={selectedProvider?.api_key_set}
                apiKeyUrl={
                  catalog.find((c) => c.id === form.catalog_id)?.api_key_url ||
                  findVendorCredential(vendorCredentials, activeFormVendor)?.api_key_url ||
                  vendors.find((v) => v.models?.some((m) => m.id === form.catalog_id))?.api_key_url
                }
                vendorApiKeySet={!!activeVendorCredential?.api_key_set}
                minimal
              />
              <div className="flex flex-wrap gap-2">
                {creating ? (
                  <button
                    type="button"
                    disabled={busyId === 'create'}
                    onClick={handleCreate}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl btn-gold text-sm"
                  >
                    <Save className="w-4 h-4" />
                    {busyId === 'create' ? '保存中…' : '保存并接入'}
                  </button>
                ) : selectedProvider ? (
                  <>
                    <button
                      type="button"
                      disabled={busyId === selectedProvider.id}
                      onClick={() => handleUpdate(selectedProvider.id)}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl btn-gold text-sm"
                    >
                      <Save className="w-4 h-4" />
                      {busyId === selectedProvider.id ? '保存中…' : '保存'}
                    </button>
                    <button
                      type="button"
                      disabled={!!busyId}
                      onClick={() => handleTest(selectedProvider.id)}
                      className="px-4 py-2.5 rounded-xl text-sm border border-purple-500/30 text-purple-300"
                    >
                      测试连通
                    </button>
                    {!selectedProvider.is_active ? (
                      <button
                        type="button"
                        disabled={!!busyId}
                        onClick={() => handleActivate(selectedProvider.id)}
                        className="px-4 py-2.5 rounded-xl text-sm border border-gold-500/30 text-gold-300"
                      >
                        设为全局默认
                      </button>
                    ) : null}
                    <button
                      type="button"
                      disabled={!!busyId}
                      onClick={() => handleDelete(selectedProvider.id)}
                      className="p-2.5 rounded-xl text-red-400 hover:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </>
                ) : null}
              </div>
            </div>
          ) : null}

          {/* 模板选择 */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-white font-medium">
                {showAllPresets ? '全部模型模板' : '常用模板'}
              </p>
              <button
                type="button"
                onClick={() => setShowAllPresets((v) => !v)}
                className="text-xs text-navy-400 hover:text-gold-300"
              >
                {showAllPresets ? '只看常用' : '显示全部'}
              </button>
            </div>
            <div className="space-y-2">
              {presetGroups.map((group) => {
                const configuredInGroup = group.items.filter((p) => p.configured).length
                const pricingInGroup = group.items.filter((p) => {
                  const row = catalog.find((c) => c.id === p.id) || p
                  return hasSavedCatalogPricing(row)
                }).length
                return (
                  <LlmVendorCollapse
                    key={group.vendor}
                    label={group.label}
                    count={group.items.length}
                    hint={`已接入 ${configuredInGroup}/${group.items.length} · 单价 ${pricingInGroup}/${group.items.length}`}
                    defaultOpen={
                      group.vendor === 'volcengine' ||
                      group.items.some((p) => LLM_RECOMMENDED_PRESET_KEYS.has(p.preset_key || p.key))
                    }
                  >
                    <LlmVendorCredentialForm
                      vendor={group.vendor}
                      credential={findVendorCredential(vendorCredentials, group.vendor)}
                      onSaved={refreshFromResponse}
                      onMessage={notify}
                    />
                    {group.items.map((preset) => {
                      const catalogRow = catalog.find((c) => c.id === preset.id) || preset
                      return (
                        <LlmModelSetupRow
                          key={preset.id || preset.preset_key}
                          preset={preset}
                          catalogRow={catalogRow}
                          pricingDraft={pricing.drafts[preset.id] || {}}
                          pricingSaving={pricing.savingId === preset.id}
                          onPatchPricing={pricing.patchDraft}
                          onSavePricing={pricing.saveRow}
                          onConnect={() => handlePresetClick(preset)}
                        />
                      )
                    })}
                  </LlmVendorCollapse>
                )
              })}
            </div>
            <button
              type="button"
              onClick={() => {
                setCreating(true)
                setEditingId(null)
                setForm({ ...EMPTY_LLM_PROVIDER })
                setApiKeyTouched(false)
              }}
              className="inline-flex items-center gap-2 text-sm text-navy-400 hover:text-gold-300"
            >
              <Plus className="w-4 h-4" />
              手动添加（非模板）
            </button>
          </div>

          <details className="rounded-xl border border-white/10 bg-slate-900/40 group">
            <summary className="cursor-pointer list-none px-4 py-3 flex items-center justify-between gap-2">
              <span className="text-sm text-navy-300 font-medium">高级运维（部署 / 批量）</span>
              <ChevronDown className="w-4 h-4 text-navy-400 transition group-open:rotate-180" />
            </summary>
            <div className="px-4 pb-4 pt-2 space-y-4 border-t border-white/5">
              <p className="text-sm text-navy-400">同步目录种子、从 .env 一键接入、测试全局默认模型。日常改 Key / 模型 ID 请在上方操作。</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={!!busyId}
                  onClick={handleSyncPresets}
                  className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-navy-200 hover:bg-white/[0.06]"
                >
                  同步目录种子
                </button>
                <button
                  type="button"
                  disabled={!!busyId}
                  onClick={handleEnvSetup}
                  className="px-4 py-2 rounded-xl btn-gold text-sm font-semibold"
                >
                  从 .env 一键接入
                </button>
                <button
                  type="button"
                  disabled={!!busyId}
                  onClick={() => handleTest(null)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm border border-purple-500/30 text-purple-300"
                >
                  <Sparkles className="w-4 h-4" />
                  测试全局默认模型
                </button>
              </div>
              {routingPlan ? (
                <div className="rounded-xl space-y-2 rounded-xl border border-white/10 p-4 text-xs text-navy-300">
                  <p className="text-white text-sm font-medium">Agent 绑定概况</p>
                  <p className="text-navy-400">
                    详细绑定请在
                    <Link to="/admin/orchestration?tab=flow" className="text-gold-400 mx-1">
                      调度中心 · 流程编排
                    </Link>
                    Tab 配置。
                  </p>
                  <div className="grid sm:grid-cols-2 gap-3 font-mono">
                    <div>
                      {Object.entries(routingPlan.nodes || {}).map(([id, meta]) => (
                        <div key={id} className="flex justify-between gap-2 py-0.5">
                          <span className="truncate">{id}</span>
                          <span className={meta.provider_id ? 'text-green-400' : 'text-amber-300'}>
                            {meta.provider_id ? '已绑' : '未绑'}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div>
                      {Object.entries(routingPlan.agents || {}).map(([id, meta]) => (
                        <div key={id} className="flex justify-between gap-2 py-0.5">
                          <span>{id}</span>
                          <span className={meta.provider_id ? 'text-green-400' : 'text-amber-300'}>
                            {meta.provider_id ? '已绑' : '未绑'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </details>
      </div>
    </motion.div>
  )
}

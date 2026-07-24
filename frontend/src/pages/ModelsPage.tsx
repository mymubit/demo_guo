import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import {
  activateProvider,
  createProvider,
  createProviderKey,
  deleteProvider,
  deleteProviderKey,
  getRoleMappings,
  listProviderKeys,
  listProviders,
  putRoleMappings,
  testProvider,
  updateProvider,
} from '@/services/v3/models'
import {
  deleteModelPrice,
  getModelPrices,
  putModelPrices,
} from '@/services/v3/prices'
import type {
  ModelPrice,
  ModelProvider,
  ModelProviderWrite,
  ProviderTestResult,
  RoleModelKey,
  RoleModelMapping,
} from '@/types/v3/domain'
import { ROLE_MODEL_KEYS } from '@/types/v3/domain'

const PROVIDERS_QUERY_KEY = ['v3', 'models', 'providers'] as const
const ROLE_MAPPINGS_QUERY_KEY = ['v3', 'models', 'role-mappings'] as const
const PRICES_QUERY_KEY = ['v3', 'models', 'prices'] as const
const providerKeysQueryKey = (providerId: string) =>
  ['v3', 'models', 'providers', providerId, 'keys'] as const

const ROLE_LABEL_ZH: Record<RoleModelKey, string> = {
  'drama-topic-director': '选题定调',
  'drama-story-bible': '故事圣经',
  'drama-episode-designer': '分集设计',
  'drama-script-writer': '剧本正文',
  'drama-script-scorer': '剧本评分',
  'drama-compliance-guard': '合规审查',
  'drama-revision-master': '剧本修订',
  'drama-delivery-tool': '宣发交付',
}

/** 与后端 models_service.MAX_BACKUP_PROVIDERS 对齐 */
const MAX_BACKUP_PROVIDERS = 5

const selectClassName =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'

type DrawerMode = 'create' | 'edit'

type ProviderFormState = {
  name: string
  base_url: string
  model_name: string
  api_key: string
  temperature: string
  max_tokens: string
  is_enabled: boolean
  remark: string
}

const EMPTY_FORM: ProviderFormState = {
  name: '',
  base_url: '',
  model_name: 'gpt-4o-mini',
  api_key: '',
  temperature: '0.7',
  max_tokens: '4096',
  is_enabled: true,
  remark: '',
}

function formFromProvider(provider: ModelProvider): ProviderFormState {
  return {
    name: provider.name,
    base_url: provider.base_url,
    model_name: provider.model_name,
    api_key: '',
    temperature: String(provider.temperature),
    max_tokens: String(provider.max_tokens),
    is_enabled: provider.is_enabled,
    remark: provider.remark || '',
  }
}

function buildWriteBody(form: ProviderFormState, mode: DrawerMode): ModelProviderWrite | string {
  const name = form.name.trim()
  if (!name) return '请填写供应商名称'

  const temperature = Number(form.temperature)
  if (!Number.isFinite(temperature) || temperature < 0 || temperature > 2) {
    return '温度须为 0–2 的数值'
  }

  const maxTokens = Number(form.max_tokens)
  if (!Number.isInteger(maxTokens) || maxTokens < 1) {
    return '最大 Token 须为正整数'
  }

  const body: ModelProviderWrite = {
    name,
    base_url: form.base_url.trim(),
    model_name: form.model_name.trim() || 'gpt-4o-mini',
    temperature,
    max_tokens: maxTokens,
    is_enabled: form.is_enabled,
    remark: form.remark.trim(),
  }

  const key = form.api_key.trim()
  if (mode === 'create') {
    if (key) body.api_key = key
  } else if (key) {
    // 编辑：仅非空时提交；空串表示不覆盖密文（也不发送字段）
    body.api_key = key
  }

  return body
}

function findProviderPrice(
  prices: ModelPrice[] | undefined,
  provider: ModelProvider,
): ModelPrice | undefined {
  return (prices ?? []).find(
    (row) => row.provider_id === provider.id && row.model_name === provider.model_name,
  )
}

function ProviderPriceEditor({
  provider,
  price,
  disabled,
}: {
  provider: ModelProvider
  price: ModelPrice | undefined
  disabled: boolean
}) {
  const queryClient = useQueryClient()
  const [priceIn, setPriceIn] = useState('')
  const [priceOut, setPriceOut] = useState('')
  const [priceCache, setPriceCache] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    setPriceIn(price != null ? String(price.price_in_per_1k) : '')
    setPriceOut(price != null ? String(price.price_out_per_1k) : '')
    setPriceCache(
      price?.price_cache_in_per_1k != null ? String(price.price_cache_in_per_1k) : '',
    )
    setLocalError(null)
  }, [
    price?.id,
    price?.price_in_per_1k,
    price?.price_out_per_1k,
    price?.price_cache_in_per_1k,
    provider.model_name,
  ])

  const saveMutation = useMutation({
    mutationFn: async (
      action:
        | { kind: 'put'; item: Parameters<typeof putModelPrices>[0]['items'][number] }
        | { kind: 'delete'; id: number },
    ) => {
      if (action.kind === 'delete') {
        return deleteModelPrice(action.id)
      }
      return putModelPrices({ items: [action.item] })
    },
    onSuccess: async () => {
      setLocalError(null)
      await queryClient.invalidateQueries({ queryKey: PRICES_QUERY_KEY })
    },
  })

  const handleSave = () => {
    setLocalError(null)
    const inTrim = priceIn.trim()
    const outTrim = priceOut.trim()
    const cacheTrim = priceCache.trim()
    if ((inTrim === '') !== (outTrim === '')) {
      setLocalError('请同时填写输入与输出单价，或都留空表示未定价')
      return
    }
    if (inTrim === '' && outTrim === '') {
      if (cacheTrim !== '') {
        setLocalError('未定价时请清空缓存命中单价')
        return
      }
      if (price?.id != null) {
        saveMutation.mutate({ kind: 'delete', id: price.id })
      }
      return
    }
    const inNum = Number(inTrim)
    const outNum = Number(outTrim)
    if (!Number.isFinite(inNum) || inNum < 0 || !Number.isFinite(outNum) || outNum < 0) {
      setLocalError('单价须为 ≥0 的数字')
      return
    }
    let cacheNum: number | null = null
    if (cacheTrim !== '') {
      cacheNum = Number(cacheTrim)
      if (!Number.isFinite(cacheNum) || cacheNum < 0) {
        setLocalError('缓存命中单价须为 ≥0 的数字，或留空按输入价计')
        return
      }
    }
    saveMutation.mutate({
      kind: 'put',
      item: {
        provider_id: provider.id,
        model_name: provider.model_name,
        price_in_per_1k: inNum,
        price_out_per_1k: outNum,
        price_cache_in_per_1k: cacheNum,
        currency: 'CNY',
      },
    })
  }

  const saveError = saveMutation.isError ? formatApiError(saveMutation.error) : null

  return (
    <div
      className="mt-3 space-y-2 border-t border-border pt-3"
      data-testid={`provider-price-${provider.id}`}
    >
      <p className="text-xs font-medium text-ink-muted">
        估算单价（元 / 1K tokens，币种 CNY）
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="block space-y-1 text-xs text-ink-muted">
          输入
          <Input
            type="number"
            min={0}
            step="any"
            inputMode="decimal"
            value={priceIn}
            onChange={(event) => setPriceIn(event.target.value)}
            disabled={disabled || saveMutation.isPending}
            aria-label={`${provider.name} 输入单价`}
            className="w-32"
          />
        </label>
        <label className="block space-y-1 text-xs text-ink-muted">
          输出
          <Input
            type="number"
            min={0}
            step="any"
            inputMode="decimal"
            value={priceOut}
            onChange={(event) => setPriceOut(event.target.value)}
            disabled={disabled || saveMutation.isPending}
            aria-label={`${provider.name} 输出单价`}
            className="w-32"
          />
        </label>
        <label className="block space-y-1 text-xs text-ink-muted">
          缓存命中
          <Input
            type="number"
            min={0}
            step="any"
            inputMode="decimal"
            value={priceCache}
            onChange={(event) => setPriceCache(event.target.value)}
            disabled={disabled || saveMutation.isPending}
            aria-label={`${provider.name} 缓存命中单价`}
            className="w-32"
            placeholder="可选"
          />
        </label>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          loading={saveMutation.isPending}
          disabled={disabled || saveMutation.isPending}
          onClick={handleSave}
          aria-label={`保存 ${provider.name} 定价`}
        >
          保存定价
        </Button>
      </div>
      <p className="text-xs text-ink-faint">
        缓存命中可留空，表示按输入单价计；有厂商折扣时单独填写更准。
      </p>
      {localError ? <p className="text-xs text-danger">{localError}</p> : null}
      {saveError ? <p className="text-xs text-danger">{saveError}</p> : null}
      {!price ? (
        <p className="text-xs text-ink-faint">当前未定价；留空保存可保持未定价。</p>
      ) : null}
    </div>
  )
}

function roleLabel(roleKey: string): string {
  if (roleKey in ROLE_LABEL_ZH) {
    return ROLE_LABEL_ZH[roleKey as RoleModelKey]
  }
  return roleKey
}

function normalizeBackupIds(
  backupIds: string[] | undefined,
  primaryId: string,
): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const id of backupIds ?? []) {
    if (!id || id === primaryId || seen.has(id)) continue
    seen.add(id)
    result.push(id)
    if (result.length >= MAX_BACKUP_PROVIDERS) break
  }
  return result
}

function moveBackupId(ids: string[], index: number, delta: number): string[] {
  const nextIndex = index + delta
  if (nextIndex < 0 || nextIndex >= ids.length) return ids
  const next = [...ids]
  const [item] = next.splice(index, 1)
  next.splice(nextIndex, 0, item)
  return next
}

export function ModelsPage() {
  const queryClient = useQueryClient()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerMode, setDrawerMode] = useState<DrawerMode>('create')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ProviderFormState>(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [mappingDraft, setMappingDraft] = useState<RoleModelMapping[]>([])
  const [backupPickByRole, setBackupPickByRole] = useState<Record<string, string>>({})
  const [testResults, setTestResults] = useState<Record<string, ProviderTestResult | { error: string }>>(
    {},
  )
  const [keysPanelProviderId, setKeysPanelProviderId] = useState<string | null>(null)
  const [newKeyLabel, setNewKeyLabel] = useState('')
  const [newKeyApiKey, setNewKeyApiKey] = useState('')
  const [newKeyError, setNewKeyError] = useState<string | null>(null)

  const providersQuery = useQuery({
    queryKey: PROVIDERS_QUERY_KEY,
    queryFn: listProviders,
  })

  const keysQuery = useQuery({
    queryKey: keysPanelProviderId
      ? providerKeysQueryKey(keysPanelProviderId)
      : ['v3', 'models', 'providers', 'keys', 'idle'],
    queryFn: () => listProviderKeys(keysPanelProviderId as string),
    enabled: Boolean(keysPanelProviderId),
  })

  const mappingsQuery = useQuery({
    queryKey: ROLE_MAPPINGS_QUERY_KEY,
    queryFn: getRoleMappings,
  })

  const pricesQuery = useQuery({
    queryKey: PRICES_QUERY_KEY,
    queryFn: getModelPrices,
  })

  const providers = providersQuery.data?.items ?? []
  const priceItems = pricesQuery.data?.items

  useEffect(() => {
    if (!mappingsQuery.data) return
    const byKey = new Map(mappingsQuery.data.items.map((item) => [item.role_key, item]))
    setMappingDraft(
      ROLE_MODEL_KEYS.map((roleKey) => {
        const existing = byKey.get(roleKey)
        const providerId = existing?.provider_id || providers[0]?.id || ''
        if (existing) {
          return {
            ...existing,
            provider_id: providerId,
            backup_provider_ids: normalizeBackupIds(existing.backup_provider_ids, providerId),
          }
        }
        return {
          role_key: roleKey,
          provider_id: providerId,
          backup_provider_ids: [],
          temperature: null,
          max_tokens: null,
        }
      }),
    )
  }, [mappingsQuery.data, providers])

  const saveProviderMutation = useMutation({
    mutationFn: async (payload: { mode: DrawerMode; id: string | null; body: ModelProviderWrite }) => {
      if (payload.mode === 'create') {
        return createProvider(payload.body)
      }
      if (!payload.id) throw new Error('缺少供应商 ID')
      return updateProvider(payload.id, payload.body)
    },
    onSuccess: async () => {
      setDrawerOpen(false)
      setFormError(null)
      await queryClient.invalidateQueries({ queryKey: PROVIDERS_QUERY_KEY })
      await queryClient.invalidateQueries({ queryKey: ROLE_MAPPINGS_QUERY_KEY })
    },
  })

  const activateMutation = useMutation({
    mutationFn: (providerId: string) => activateProvider(providerId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: PROVIDERS_QUERY_KEY })
      await queryClient.invalidateQueries({ queryKey: ROLE_MAPPINGS_QUERY_KEY })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (providerId: string) => deleteProvider(providerId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: PROVIDERS_QUERY_KEY })
      await queryClient.invalidateQueries({ queryKey: ROLE_MAPPINGS_QUERY_KEY })
    },
  })

  const testMutation = useMutation({
    mutationFn: (providerId: string) => testProvider(providerId),
    onSuccess: (result, providerId) => {
      setTestResults((prev) => ({ ...prev, [providerId]: result }))
    },
    onError: (error, providerId) => {
      setTestResults((prev) => ({
        ...prev,
        [providerId]: { error: formatApiError(error) },
      }))
    },
  })

  const createKeyMutation = useMutation({
    mutationFn: (payload: { providerId: string; label: string; api_key: string }) =>
      createProviderKey(payload.providerId, {
        label: payload.label,
        api_key: payload.api_key,
      }),
    onSuccess: async (_data, variables) => {
      setNewKeyLabel('')
      setNewKeyApiKey('')
      setNewKeyError(null)
      await queryClient.invalidateQueries({
        queryKey: providerKeysQueryKey(variables.providerId),
      })
    },
  })

  const deleteKeyMutation = useMutation({
    mutationFn: (payload: { providerId: string; keyId: string }) =>
      deleteProviderKey(payload.providerId, payload.keyId),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: providerKeysQueryKey(variables.providerId),
      })
    },
  })

  const handleDeleteProvider = (provider: ModelProvider) => {
    const confirmed = window.confirm(`确定删除供应商「${provider.name}」？此操作不可恢复。`)
    if (!confirmed) return
    deleteMutation.mutate(provider.id)
  }

  const saveMappingsMutation = useMutation({
    mutationFn: () => {
      const items = mappingDraft
        .filter((item) => item.provider_id)
        .map((item) => ({
          role_key: item.role_key,
          provider_id: item.provider_id,
          backup_provider_ids: normalizeBackupIds(item.backup_provider_ids, item.provider_id),
          ...(item.temperature != null ? { temperature: item.temperature } : {}),
          ...(item.max_tokens != null ? { max_tokens: item.max_tokens } : {}),
        }))
      return putRoleMappings({ items })
    },
    onSuccess: async (next) => {
      queryClient.setQueryData(ROLE_MAPPINGS_QUERY_KEY, next)
      await queryClient.invalidateQueries({ queryKey: ROLE_MAPPINGS_QUERY_KEY })
    },
  })

  const updateRolePrimary = (roleKey: string, providerId: string) => {
    setMappingDraft((prev) =>
      prev.map((row) =>
        row.role_key === roleKey
          ? {
              ...row,
              provider_id: providerId,
              backup_provider_ids: normalizeBackupIds(row.backup_provider_ids, providerId),
            }
          : row,
      ),
    )
  }

  const addRoleBackup = (roleKey: string, providerId: string) => {
    if (!providerId) return
    setMappingDraft((prev) =>
      prev.map((row) => {
        if (row.role_key !== roleKey) return row
        const current = normalizeBackupIds(row.backup_provider_ids, row.provider_id)
        if (providerId === row.provider_id || current.includes(providerId)) return row
        if (current.length >= MAX_BACKUP_PROVIDERS) return row
        return { ...row, backup_provider_ids: [...current, providerId] }
      }),
    )
    setBackupPickByRole((prev) => ({ ...prev, [roleKey]: '' }))
  }

  const moveRoleBackup = (roleKey: string, index: number, delta: number) => {
    setMappingDraft((prev) =>
      prev.map((row) => {
        if (row.role_key !== roleKey) return row
        const current = normalizeBackupIds(row.backup_provider_ids, row.provider_id)
        return { ...row, backup_provider_ids: moveBackupId(current, index, delta) }
      }),
    )
  }

  const removeRoleBackup = (roleKey: string, providerId: string) => {
    setMappingDraft((prev) =>
      prev.map((row) =>
        row.role_key === roleKey
          ? {
              ...row,
              backup_provider_ids: (row.backup_provider_ids ?? []).filter((id) => id !== providerId),
            }
          : row,
      ),
    )
  }

  const providerNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const provider of providers) {
      map.set(provider.id, provider.name)
    }
    return map
  }, [providers])

  const openCreate = () => {
    setDrawerMode('create')
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
    setDrawerOpen(true)
  }

  const openEdit = (provider: ModelProvider) => {
    setDrawerMode('edit')
    setEditingId(provider.id)
    setForm(formFromProvider(provider))
    setFormError(null)
    setDrawerOpen(true)
  }

  const handleDrawerSubmit = (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)
    const body = buildWriteBody(form, drawerMode)
    if (typeof body === 'string') {
      setFormError(body)
      return
    }
    saveProviderMutation.mutate({ mode: drawerMode, id: editingId, body })
  }

  const toggleKeysPanel = (providerId: string) => {
    setNewKeyError(null)
    setNewKeyLabel('')
    setNewKeyApiKey('')
    setKeysPanelProviderId((prev) => (prev === providerId ? null : providerId))
  }

  const handleAddKey = (providerId: string) => {
    setNewKeyError(null)
    const label = newKeyLabel.trim()
    const apiKey = newKeyApiKey.trim()
    if (!label) {
      setNewKeyError('请填写密钥标签')
      return
    }
    if (!apiKey) {
      setNewKeyError('请填写 API Key')
      return
    }
    createKeyMutation.mutate({ providerId, label, api_key: apiKey })
  }

  const handleDeleteKey = (providerId: string, keyId: string, label: string) => {
    const confirmed = window.confirm(`确定删除附加密钥「${label}」？此操作不可恢复。`)
    if (!confirmed) return
    deleteKeyMutation.mutate({ providerId, keyId })
  }

  const busy =
    saveProviderMutation.isPending ||
    activateMutation.isPending ||
    deleteMutation.isPending ||
    saveMappingsMutation.isPending ||
    createKeyMutation.isPending ||
    deleteKeyMutation.isPending

  const actionError = useMemo(() => {
    if (saveProviderMutation.isError) return formatApiError(saveProviderMutation.error)
    if (activateMutation.isError) return formatApiError(activateMutation.error)
    if (deleteMutation.isError) return formatApiError(deleteMutation.error)
    if (saveMappingsMutation.isError) return formatApiError(saveMappingsMutation.error)
    if (createKeyMutation.isError) return formatApiError(createKeyMutation.error)
    if (deleteKeyMutation.isError) return formatApiError(deleteKeyMutation.error)
    return null
  }, [
    activateMutation.error,
    activateMutation.isError,
    createKeyMutation.error,
    createKeyMutation.isError,
    deleteKeyMutation.error,
    deleteKeyMutation.isError,
    deleteMutation.error,
    deleteMutation.isError,
    saveMappingsMutation.error,
    saveMappingsMutation.isError,
    saveProviderMutation.error,
    saveProviderMutation.isError,
  ])

  const actions = (
    <Button type="button" onClick={openCreate}>
      新建供应商
    </Button>
  )

  return (
    <PageShell
      title="模型配置"
      description="管理模型供应商、主密钥与附加密钥轮询、角色映射。密钥仅可写入，永不回显明文。"
      actions={actions}
    >
      {providersQuery.isLoading || mappingsQuery.isLoading || pricesQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载模型配置…</p>
      ) : null}

      {providersQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(providersQuery.error)}</p>
      ) : null}
      {mappingsQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(mappingsQuery.error)}</p>
      ) : null}
      {pricesQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(pricesQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {!providersQuery.isLoading && !providersQuery.isError ? (
        <div className="space-y-6">
          <section className="sf-panel space-y-3 p-4">
            <h2 className="text-sm font-semibold text-ink">供应商列表</h2>
            {providers.length === 0 ? (
              <p className="text-sm text-ink-muted">尚未配置供应商，请点击「新建供应商」。</p>
            ) : (
              <ul className="space-y-3">
                {providers.map((provider) => {
                  const result = testResults[provider.id]
                  return (
                    <li
                      key={provider.id}
                      className="rounded-md border border-border px-4 py-3"
                      data-testid={`provider-row-${provider.id}`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-sm font-semibold text-ink">{provider.name}</h3>
                            {provider.is_active ? (
                              <span className="text-xs font-medium text-action">当前激活</span>
                            ) : null}
                            {!provider.is_enabled ? (
                              <span className="text-xs text-ink-faint">已停用</span>
                            ) : null}
                          </div>
                          <p className="text-xs text-ink-muted">
                            {provider.model_name}
                            {provider.base_url ? ` · ${provider.base_url}` : ''}
                          </p>
                          <p className="text-xs text-ink-muted">
                            密钥：{provider.api_key_set ? '已配置' : '未配置'}
                            {' · '}
                            温度：{provider.temperature}
                            {' · '}
                            最大 Token：{provider.max_tokens}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            onClick={() => openEdit(provider)}
                            disabled={busy}
                          >
                            编辑
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            onClick={() => toggleKeysPanel(provider.id)}
                            disabled={busy}
                            aria-label={`管理 ${provider.name} 附加密钥`}
                            aria-expanded={keysPanelProviderId === provider.id}
                          >
                            {keysPanelProviderId === provider.id ? '收起密钥' : '附加密钥'}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            loading={
                              testMutation.isPending && testMutation.variables === provider.id
                            }
                            onClick={() => testMutation.mutate(provider.id)}
                            disabled={busy || !provider.api_key_set}
                            aria-label={`试连 ${provider.name}`}
                          >
                            试连
                          </Button>
                          {!provider.is_active ? (
                            <Button
                              type="button"
                              size="sm"
                              loading={
                                activateMutation.isPending &&
                                activateMutation.variables === provider.id
                              }
                              onClick={() => activateMutation.mutate(provider.id)}
                              disabled={busy || !provider.is_enabled}
                              aria-label={`激活 ${provider.name}`}
                            >
                              设为激活
                            </Button>
                          ) : null}
                          <Button
                            type="button"
                            size="sm"
                            variant="danger"
                            loading={
                              deleteMutation.isPending && deleteMutation.variables === provider.id
                            }
                            onClick={() => handleDeleteProvider(provider)}
                            disabled={busy}
                            aria-label={`删除 ${provider.name}`}
                          >
                            删除
                          </Button>
                        </div>
                      </div>
                      {result ? (
                        <p
                          className={
                            'error' in result
                              ? 'mt-2 text-xs text-danger'
                              : result.ok
                                ? 'mt-2 text-xs text-action'
                                : 'mt-2 text-xs text-danger'
                          }
                          data-testid={`test-result-${provider.id}`}
                        >
                          {'error' in result
                            ? `试连失败：${result.error}`
                            : `${result.message}${
                                result.latency_ms != null ? ` · ${result.latency_ms} ms` : ''
                              }`}
                        </p>
                      ) : null}

                      <ProviderPriceEditor
                        provider={provider}
                        price={findProviderPrice(priceItems, provider)}
                        disabled={busy}
                      />

                      {keysPanelProviderId === provider.id ? (
                        <div
                          className="mt-3 space-y-3 border-t border-border pt-3"
                          data-testid={`provider-keys-${provider.id}`}
                        >
                          <p className="text-xs text-ink-muted">
                            附加密钥按排序轮询；主密钥仍在供应商编辑中配置。列表仅显示是否已配置，永不回显明文。
                          </p>
                          {keysQuery.isLoading ? (
                            <p className="text-xs text-ink-faint">正在加载附加密钥…</p>
                          ) : null}
                          {keysQuery.isError ? (
                            <p className="text-xs text-danger">
                              {formatApiError(keysQuery.error)}
                            </p>
                          ) : null}
                          {(keysQuery.data?.items ?? []).length === 0 && !keysQuery.isLoading ? (
                            <p className="text-xs text-ink-faint">暂无附加密钥。</p>
                          ) : (
                            <ul className="space-y-2">
                              {(keysQuery.data?.items ?? []).map((keyRow) => (
                                <li
                                  key={keyRow.id}
                                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-border/70 px-3 py-2"
                                  data-testid={`provider-key-${keyRow.id}`}
                                >
                                  <span className="text-sm text-ink">
                                    {keyRow.label}
                                    <span className="ml-2 text-xs text-ink-faint">
                                      排序 {keyRow.sort_order}
                                      {' · '}
                                      {keyRow.api_key_set ? '已配置' : '未配置'}
                                      {!keyRow.is_enabled ? ' · 已停用' : ''}
                                    </span>
                                  </span>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="danger"
                                    disabled={busy}
                                    loading={
                                      deleteKeyMutation.isPending &&
                                      deleteKeyMutation.variables?.keyId === keyRow.id
                                    }
                                    aria-label={`删除附加密钥 ${keyRow.label}`}
                                    onClick={() =>
                                      handleDeleteKey(provider.id, keyRow.id, keyRow.label)
                                    }
                                  >
                                    删除
                                  </Button>
                                </li>
                              ))}
                            </ul>
                          )}
                          <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                            <label className="block space-y-1 text-xs font-medium text-ink-muted">
                              标签
                              <Input
                                value={newKeyLabel}
                                onChange={(event) => setNewKeyLabel(event.target.value)}
                                disabled={createKeyMutation.isPending}
                                aria-label={`${provider.name} 附加密钥标签`}
                                placeholder="例如：备用线路"
                              />
                            </label>
                            <label className="block space-y-1 text-xs font-medium text-ink-muted">
                              API Key
                              <Input
                                type="password"
                                value={newKeyApiKey}
                                onChange={(event) => setNewKeyApiKey(event.target.value)}
                                disabled={createKeyMutation.isPending}
                                autoComplete="off"
                                aria-label={`${provider.name} 附加密钥 API Key`}
                                placeholder="写入后不会回显"
                              />
                            </label>
                            <div className="flex items-end">
                              <Button
                                type="button"
                                size="sm"
                                loading={createKeyMutation.isPending}
                                disabled={busy}
                                aria-label={`添加 ${provider.name} 附加密钥`}
                                onClick={() => handleAddKey(provider.id)}
                              >
                                添加密钥
                              </Button>
                            </div>
                          </div>
                          {newKeyError ? (
                            <p className="text-xs text-danger">{newKeyError}</p>
                          ) : null}
                        </div>
                      ) : null}
                    </li>
                  )
                })}
              </ul>
            )}
          </section>

          <section className="sf-panel space-y-3 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-ink">角色映射</h2>
              <Button
                type="button"
                size="sm"
                loading={saveMappingsMutation.isPending}
                onClick={() => saveMappingsMutation.mutate()}
                disabled={busy || providers.length === 0 || mappingDraft.some((item) => !item.provider_id)}
              >
                保存映射
              </Button>
            </div>
            <p className="text-xs text-ink-faint">
              未单独配置的角色默认使用当前激活供应商。可为各角色指定主供应商与有序备选（故障时可自动切换）。
            </p>
            {providers.length === 0 ? (
              <p className="text-sm text-ink-muted">请先创建至少一个供应商。</p>
            ) : (
              <ul className="space-y-4">
                {mappingDraft.map((item) => {
                  const label = roleLabel(item.role_key)
                  const backups = normalizeBackupIds(item.backup_provider_ids, item.provider_id)
                  const excluded = new Set<string>([item.provider_id, ...backups])
                  const addCandidates = providers.filter((provider) => !excluded.has(provider.id))
                  const pickValue = backupPickByRole[item.role_key] ?? ''
                  const canAdd =
                    Boolean(pickValue) &&
                    backups.length < MAX_BACKUP_PROVIDERS &&
                    addCandidates.some((provider) => provider.id === pickValue)

                  return (
                    <li
                      key={item.role_key}
                      className="rounded-md border border-border px-4 py-3"
                      data-testid={`role-mapping-${item.role_key}`}
                    >
                      <div className="mb-3 flex flex-wrap items-baseline gap-2">
                        <span className="text-sm font-medium text-ink">{label}</span>
                        <span className="text-xs text-ink-faint">{item.role_key}</span>
                      </div>

                      <label className="mb-3 block space-y-1.5 text-xs font-medium text-ink-muted">
                        主供应商
                        <select
                          className={selectClassName}
                          value={item.provider_id}
                          aria-label={`角色 ${label} 的主供应商`}
                          disabled={busy}
                          onChange={(event) => updateRolePrimary(item.role_key, event.target.value)}
                        >
                          <option value="">请选择</option>
                          {providers.map((provider) => (
                            <option key={provider.id} value={provider.id}>
                              {provider.name}
                              {provider.is_active ? '（激活）' : ''}
                            </option>
                          ))}
                        </select>
                      </label>

                      <div className="space-y-2">
                        <p className="text-xs font-medium text-ink-muted">备选供应商</p>
                        {backups.length === 0 ? (
                          <p className="text-xs text-ink-faint">暂无备选，失败时可按顺序切换。</p>
                        ) : (
                          <ol className="space-y-2">
                            {backups.map((backupId, index) => {
                              const backupName = providerNameById.get(backupId) ?? backupId
                              return (
                                <li
                                  key={`${item.role_key}-${backupId}`}
                                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-border/70 px-3 py-2"
                                >
                                  <span className="text-sm text-ink">
                                    <span className="mr-2 text-xs text-ink-faint">{index + 1}.</span>
                                    {backupName}
                                  </span>
                                  <div className="flex flex-wrap gap-1">
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="secondary"
                                      disabled={busy || index === 0}
                                      aria-label={`角色 ${label} ${backupName} 上移`}
                                      onClick={() => moveRoleBackup(item.role_key, index, -1)}
                                    >
                                      上移
                                    </Button>
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="secondary"
                                      disabled={busy || index === backups.length - 1}
                                      aria-label={`角色 ${label} ${backupName} 下移`}
                                      onClick={() => moveRoleBackup(item.role_key, index, 1)}
                                    >
                                      下移
                                    </Button>
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="danger"
                                      disabled={busy}
                                      aria-label={`角色 ${label} ${backupName} 删除`}
                                      onClick={() => removeRoleBackup(item.role_key, backupId)}
                                    >
                                      删除
                                    </Button>
                                  </div>
                                </li>
                              )
                            })}
                          </ol>
                        )}

                        <div className="flex flex-wrap items-end gap-2 pt-1">
                          <label className="min-w-[12rem] flex-1 space-y-1.5 text-xs font-medium text-ink-muted">
                            添加备选
                            <select
                              className={selectClassName}
                              value={pickValue}
                              aria-label={`角色 ${label} 添加备选`}
                              disabled={
                                busy ||
                                addCandidates.length === 0 ||
                                backups.length >= MAX_BACKUP_PROVIDERS
                              }
                              onChange={(event) =>
                                setBackupPickByRole((prev) => ({
                                  ...prev,
                                  [item.role_key]: event.target.value,
                                }))
                              }
                            >
                              <option value="">请选择备选供应商</option>
                              {addCandidates.map((provider) => (
                                <option key={provider.id} value={provider.id}>
                                  {provider.name}
                                  {provider.is_active ? '（激活）' : ''}
                                </option>
                              ))}
                            </select>
                          </label>
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            disabled={busy || !canAdd}
                            aria-label={`角色 ${label} 添加备选供应商`}
                            onClick={() => addRoleBackup(item.role_key, pickValue)}
                          >
                            添加
                          </Button>
                        </div>
                        {backups.length >= MAX_BACKUP_PROVIDERS ? (
                          <p className="text-xs text-ink-faint">
                            最多 {MAX_BACKUP_PROVIDERS} 个备选供应商。
                          </p>
                        ) : null}
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </div>
      ) : null}

      <Dialog open={drawerOpen} onOpenChange={setDrawerOpen}>
        <DialogContent
          className="fixed inset-y-0 right-0 left-auto top-0 flex h-full max-h-none w-full max-w-md translate-x-0 translate-y-0 flex-col gap-0 overflow-y-auto rounded-none border-l sm:rounded-none data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right"
          aria-describedby={undefined}
        >
          <DialogHeader>
            <DialogTitle>{drawerMode === 'create' ? '新建供应商' : '编辑供应商'}</DialogTitle>
            <DialogDescription>
              {drawerMode === 'create'
                ? '填写供应商与调用参数。API Key 仅写入，列表中只显示是否已配置。'
                : '留空 API Key 表示不修改已有密钥。'}
            </DialogDescription>
          </DialogHeader>
          <form className="mt-4 flex flex-1 flex-col gap-4" onSubmit={handleDrawerSubmit}>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              名称
              <Input
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                required
                disabled={saveProviderMutation.isPending}
                aria-label="供应商名称"
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              Base URL
              <Input
                value={form.base_url}
                onChange={(event) => setForm((prev) => ({ ...prev, base_url: event.target.value }))}
                placeholder="https://api.example.com/v1"
                disabled={saveProviderMutation.isPending}
                aria-label="Base URL"
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              模型名称
              <Input
                value={form.model_name}
                onChange={(event) => setForm((prev) => ({ ...prev, model_name: event.target.value }))}
                disabled={saveProviderMutation.isPending}
                aria-label="模型名称"
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              API Key
              <Input
                type="password"
                value={form.api_key}
                onChange={(event) => setForm((prev) => ({ ...prev, api_key: event.target.value }))}
                placeholder={
                  drawerMode === 'edit' ? '留空则不修改已有密钥' : '可选，写入后不会回显'
                }
                autoComplete="off"
                disabled={saveProviderMutation.isPending}
                aria-label="API Key"
              />
              <span className="block text-xs font-normal text-ink-faint">
                密钥仅可写入，界面永不展示明文。
              </span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                温度
                <Input
                  type="number"
                  min={0}
                  max={2}
                  step="0.1"
                  value={form.temperature}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, temperature: event.target.value }))
                  }
                  disabled={saveProviderMutation.isPending}
                  aria-label="温度"
                />
              </label>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                最大 Token
                <Input
                  type="number"
                  min={1}
                  step={1}
                  value={form.max_tokens}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, max_tokens: event.target.value }))
                  }
                  disabled={saveProviderMutation.isPending}
                  aria-label="最大 Token"
                />
              </label>
            </div>
            <label className="flex items-center gap-2 text-sm font-medium text-ink">
              <input
                type="checkbox"
                checked={form.is_enabled}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, is_enabled: event.target.checked }))
                }
                disabled={saveProviderMutation.isPending}
                aria-label="启用供应商"
              />
              启用
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              备注
              <Input
                value={form.remark}
                onChange={(event) => setForm((prev) => ({ ...prev, remark: event.target.value }))}
                disabled={saveProviderMutation.isPending}
                aria-label="备注"
              />
            </label>
            {formError ? <p className="text-sm text-danger">{formError}</p> : null}
            {saveProviderMutation.isError ? (
              <p className="text-sm text-danger">{formatApiError(saveProviderMutation.error)}</p>
            ) : null}
            <DialogFooter className="mt-auto">
              <Button
                type="button"
                variant="secondary"
                disabled={saveProviderMutation.isPending}
                onClick={() => setDrawerOpen(false)}
              >
                取消
              </Button>
              <Button type="submit" loading={saveProviderMutation.isPending}>
                {drawerMode === 'create' ? '创建' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </PageShell>
  )
}

import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ExternalLink, Plus, Save, Trash2, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import {
  DEFAULT_LLM_FORM,
  groupPresetsByVendor,
  LLM_VENDOR_PRESETS,
  type LlmVendorPreset,
} from '@/config/llmPresets'
import {
  adminApi,
  type LlmProviderItem,
  type LlmProviderWritePayload,
} from '@/services/admin'
import { formatApiError } from '@/services/errors'
import { cn } from '@/utils/cn'

/** 早期联调留下的海外/演示配置，国内环境通常不可用 */
function isLikelyDemoOverseas(item: LlmProviderItem): boolean {
  const url = (item.base_url || '').toLowerCase()
  const name = (item.name || '').toLowerCase()
  return (
    url.includes('api.openai.com') ||
    name.includes('demo-openai') ||
    (name.startsWith('demo-') && url.includes('openai'))
  )
}

export function ModelHubPage() {
  const qc = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<LlmProviderWritePayload>({ ...DEFAULT_LLM_FORM })
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const vendorGroups = useMemo(() => groupPresetsByVendor(), [])

  const query = useQuery({
    queryKey: ['admin-llm-providers'],
    queryFn: () => adminApi.getLlmProviders(),
  })

  useEffect(() => {
    if (!editingId) {
      setForm({ ...DEFAULT_LLM_FORM })
      setSelectedPresetId(null)
      return
    }
    const item = query.data?.providers.find((p) => p.id === editingId)
    if (!item) return
    setSelectedPresetId(null)
    setForm({
      name: item.name,
      base_url: item.base_url,
      model_name: item.model_name,
      api_key: '',
      temperature: item.temperature,
      max_tokens: item.max_tokens,
      is_enabled: item.is_enabled,
      is_active: item.is_active,
      remark: item.remark,
    })
  }, [editingId, query.data])

  function applyPreset(preset: LlmVendorPreset) {
    setEditingId(null)
    setSelectedPresetId(preset.id)
    setForm({
      ...DEFAULT_LLM_FORM,
      name: preset.name,
      base_url: preset.base_url,
      model_name: preset.model_name,
      temperature: preset.temperature,
      max_tokens: preset.max_tokens,
      remark: preset.remark || '',
      is_active: (query.data?.providers.length ?? 0) === 0,
    })
    setMessage(`已填入「${preset.vendorLabel} · ${preset.name}」，请填写 API Key 后保存`)
    setError(null)
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!form.name.trim()) throw new Error('请填写展示名称')
      if (!form.base_url?.trim()) throw new Error('请填写接口地址')
      if (!editingId && !form.api_key?.trim()) throw new Error('请填写 API Key')
      if (editingId) {
        const payload: Partial<LlmProviderWritePayload> = { ...form }
        if (!payload.api_key?.trim()) delete payload.api_key
        return adminApi.updateLlmProvider(editingId, payload)
      }
      return adminApi.createLlmProvider(form)
    },
    onSuccess: async () => {
      setMessage(editingId ? '已更新模型配置' : '已创建模型配置')
      setError(null)
      setEditingId(null)
      setSelectedPresetId(null)
      setForm({ ...DEFAULT_LLM_FORM })
      await qc.invalidateQueries({ queryKey: ['admin-llm-providers'] })
    },
    onError: (err) => {
      setError(formatApiError(err))
      setMessage(null)
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: string) => adminApi.activateLlmProvider(id),
    onSuccess: async () => {
      setMessage('已设为当前使用模型')
      await qc.invalidateQueries({ queryKey: ['admin-llm-providers'] })
    },
    onError: (err) => setError(formatApiError(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteLlmProvider(id),
    onSuccess: async () => {
      setMessage('已删除')
      if (editingId) setEditingId(null)
      await qc.invalidateQueries({ queryKey: ['admin-llm-providers'] })
    },
    onError: (err) => setError(formatApiError(err)),
  })

  const testMutation = useMutation({
    mutationFn: (id: string) => adminApi.testLlmProvider(id),
    onSuccess: (data) => {
      if (data.ok) setMessage(`连通成功（HTTP ${data.status_code ?? 200}）`)
      else setError(data.error || data.detail || '连通失败')
    },
    onError: (err) => setError(formatApiError(err)),
  })

  const cleanupDemoMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      for (const id of ids) {
        await adminApi.deleteLlmProvider(id)
      }
      return ids.length
    },
    onSuccess: async (count) => {
      setMessage(`已清理 ${count} 条演示/海外 OpenAI 配置。请选用国内预设并填写 Key。`)
      setError(null)
      setEditingId(null)
      await qc.invalidateQueries({ queryKey: ['admin-llm-providers'] })
    },
    onError: (err) => setError(formatApiError(err)),
  })

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    saveMutation.mutate()
  }

  function startEdit(item: LlmProviderItem) {
    setEditingId(item.id)
    setMessage(null)
    setError(null)
  }

  const runtime = query.data?.runtime
  const providers = query.data?.providers ?? []
  const demoOverseas = useMemo(() => providers.filter(isLikelyDemoOverseas), [providers])
  const activePreset = selectedPresetId
    ? LLM_VENDOR_PRESETS.find((p) => p.id === selectedPresetId)
    : undefined

  return (
    <PageShell
      title="模型管理"
      description="优先接入国内主流大模型（DeepSeek / 通义 / 智谱 / Kimi / 豆包）。密钥仅写入不回显。"
      actions={
        <Link to="/admin/config" className="text-sm text-action underline-offset-2 hover:underline">
          技能覆盖配置 →
        </Link>
      }
    >
      <div className="space-y-6">
        {query.isLoading ? <LoadingBlock /> : null}
        {error ? <ErrorBanner message={error} /> : null}
        {message ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {message}
          </div>
        ) : null}

        {runtime ? (
          <div className="sf-panel px-5 py-4">
            <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">运行时状态</div>
            <div className="mt-2 flex flex-wrap gap-4 text-sm text-ink">
              <span>
                状态：
                <strong>
                  {runtime.status === 'enabled'
                    ? '已启用'
                    : runtime.status === 'disabled'
                      ? '已禁用'
                      : '配置不完整'}
                </strong>
              </span>
              <span>
                来源：
                <strong>
                  {runtime.source === 'db' ? '后台配置' : runtime.source === 'env' ? '环境变量' : '无'}
                </strong>
              </span>
              <span>
                模型：<strong>{runtime.model || '—'}</strong>
              </span>
              <span>
                Key：<strong>{runtime.api_key_set ? '已配置' : '未配置'}</strong>
              </span>
            </div>
            {runtime.base_url?.includes('openai.com') ? (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                当前活跃接口指向 OpenAI 官方地址。国内网络下可能不通；建议下方选用 DeepSeek / 通义 /
                智谱等预设，填写国内 Key 后设为「当前使用」。
              </div>
            ) : null}
          </div>
        ) : null}

        {demoOverseas.length > 0 ? (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-900">
            <p>
              检测到 {demoOverseas.length} 条演示/海外 OpenAI 配置（联调残留），可能影响真实生成。
            </p>
            <Button
              size="sm"
              variant="secondary"
              loading={cleanupDemoMutation.isPending}
              onClick={() => {
                if (
                  window.confirm(
                    `将删除 ${demoOverseas.length} 条演示/OpenAI 配置，不可恢复。确认清理？`,
                  )
                ) {
                  cleanupDemoMutation.mutate(demoOverseas.map((p) => p.id))
                }
              }}
            >
              一键清理演示配置
            </Button>
          </div>
        ) : null}

        <section className="sf-panel p-5">
          <h2 className="text-sm font-semibold text-ink">一键填入国内厂商预设</h2>
          <p className="mt-1 text-xs text-ink-muted">点击后自动填充接口地址与模型名，再粘贴你的 API Key 即可。</p>
          <div className="mt-4 space-y-4">
            {vendorGroups.map((group) => (
              <div key={group.vendor}>
                <div className="mb-2 text-xs font-medium text-ink-muted">{group.vendorLabel}</div>
                <div className="flex flex-wrap gap-2">
                  {group.items.map((preset) => (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => applyPreset(preset)}
                      className={cn(
                        'rounded-lg border px-3 py-1.5 text-sm transition',
                        selectedPresetId === preset.id
                          ? 'border-action bg-action text-white'
                          : 'border-border bg-canvas-muted text-ink hover:border-action/40 hover:bg-surface',
                      )}
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-ink">已保存配置</h2>
              <Button
                size="sm"
                variant="secondary"
                iconLeft={<Plus className="h-3.5 w-3.5" />}
                onClick={() => {
                  setEditingId(null)
                  setSelectedPresetId(null)
                  setForm({ ...DEFAULT_LLM_FORM, is_active: providers.length === 0 })
                }}
              >
                空白新建
              </Button>
            </div>
            {providers.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border px-4 py-8 text-center text-sm text-ink-muted">
                暂无配置。请上方点选国内厂商预设，填写 Key 后保存。
              </div>
            ) : (
              <ul className="space-y-2">
                {providers.map((item) => (
                  <li key={item.id} className="sf-panel px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <button type="button" className="min-w-0 text-left" onClick={() => startEdit(item)}>
                        <div className="truncate font-medium text-ink">
                          {item.name}
                          {item.is_active ? (
                            <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-[11px] text-emerald-700">
                              当前
                            </span>
                          ) : null}
                          {!item.is_enabled ? (
                            <span className="ml-2 rounded bg-canvas-muted px-1.5 py-0.5 text-[11px] text-ink-muted">
                              已停用
                            </span>
                          ) : null}
                          {isLikelyDemoOverseas(item) ? (
                            <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-[11px] text-amber-800">
                              演示/海外
                            </span>
                          ) : null}
                        </div>
                        <div className="mt-1 truncate text-xs text-ink-muted">
                          {item.model_name} · {item.base_url || '未填接口地址'} · Key{' '}
                          {item.api_key_set ? '已设' : '未设'}
                        </div>
                      </button>
                      <div className="flex shrink-0 gap-1">
                        {!item.is_active ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => activateMutation.mutate(item.id)}
                            disabled={activateMutation.isPending}
                          >
                            设为当前
                          </Button>
                        ) : null}
                        <Button
                          size="sm"
                          variant="ghost"
                          iconLeft={<Zap className="h-3.5 w-3.5" />}
                          onClick={() => testMutation.mutate(item.id)}
                          disabled={testMutation.isPending}
                        >
                          探测
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          iconLeft={<Trash2 className="h-3.5 w-3.5" />}
                          onClick={() => {
                            if (window.confirm(`确认删除「${item.name}」？`)) {
                              deleteMutation.mutate(item.id)
                            }
                          }}
                        >
                          删除
                        </Button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="sf-panel p-5">
            <h2 className="text-sm font-semibold text-ink">
              {editingId ? '编辑配置' : selectedPresetId ? '按预设新建' : '新建配置'}
            </h2>
            {activePreset ? (
              <a
                href={activePreset.apiKeyUrl}
                target="_blank"
                rel="noreferrer"
                className="mt-1 inline-flex items-center gap-1 text-xs text-action hover:underline"
              >
                前往获取 {activePreset.apiKeyHint}
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : null}
            <form className="mt-4 space-y-3" onSubmit={onSubmit}>
              <label className="block">
                <span className="sf-label">展示名称</span>
                <input
                  className="sf-control"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </label>
              <label className="block">
                <span className="sf-label">接口地址（Base URL）</span>
                <input
                  className="sf-control"
                  placeholder="例如 https://api.deepseek.com"
                  value={form.base_url || ''}
                  onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                  required
                />
              </label>
              <label className="block">
                <span className="sf-label">模型名称</span>
                <input
                  className="sf-control"
                  value={form.model_name || ''}
                  onChange={(e) => setForm({ ...form, model_name: e.target.value })}
                  required
                />
              </label>
              <label className="block">
                <span className="sf-label">
                  API Key{editingId ? '（留空则不修改）' : ''}
                </span>
                <input
                  className="sf-control"
                  type="password"
                  autoComplete="new-password"
                  value={form.api_key || ''}
                  onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  placeholder={editingId ? '••••••••' : activePreset?.apiKeyHint || '粘贴密钥'}
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="sf-label">温度</span>
                  <input
                    className="sf-control"
                    type="number"
                    step="0.1"
                    min={0}
                    max={2}
                    value={form.temperature ?? 0.7}
                    onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })}
                  />
                </label>
                <label className="block">
                  <span className="sf-label">最大 Token</span>
                  <input
                    className="sf-control"
                    type="number"
                    min={1}
                    value={form.max_tokens ?? 8192}
                    onChange={(e) => setForm({ ...form, max_tokens: Number(e.target.value) })}
                  />
                </label>
              </div>
              <label className="flex items-center gap-2 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={Boolean(form.is_enabled)}
                  onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
                />
                启用此配置
              </label>
              <label className="flex items-center gap-2 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={Boolean(form.is_active)}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                设为当前使用
              </label>
              <label className="block">
                <span className="sf-label">备注</span>
                <input
                  className="sf-control"
                  value={form.remark || ''}
                  onChange={(e) => setForm({ ...form, remark: e.target.value })}
                />
              </label>
              <Button
                type="submit"
                variant="action"
                className="w-full"
                iconLeft={<Save className="h-4 w-4" />}
                disabled={saveMutation.isPending}
              >
                {saveMutation.isPending ? '保存中…' : '保存'}
              </Button>
            </form>
          </section>
        </div>
      </div>
    </PageShell>
  )
}

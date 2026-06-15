import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshCw, Plus, Save, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { admin, useConfigStore } from '@/services/api'
import AdminShell from '@/components/admin/AdminShell'
import {
  AdminBadge,
  AdminConfirmDialog,
  AdminLoading,
  AdminMessage,
  AdminPagination,
  AdminSearchInput,
  AdminStatGrid,
  AdminTable,
  AdminToolbar,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { ICON } from '@/constants/iconSizes'

const VALUE_TYPES = [
  { value: 'string', label: '字符串' },
  { value: 'int', label: '整数' },
  { value: 'float', label: '小数' },
  { value: 'bool', label: '布尔' },
  { value: 'json', label: 'JSON对象' },
  { value: 'array', label: 'JSON数组' },
]

const EMPTY_FORM = {
  category: '',
  config_key: '',
  config_name: '',
  value_type: 'string',
  value: '',
  default_value: '',
  description: '',
  validation_schema: '{}',
  is_active: true,
  is_public: false,
  is_sensitive: false,
  requires_restart: false,
  change_reason: '',
}

function stringifyValue(value, valueType) {
  if (valueType === 'json' || valueType === 'array') {
    return JSON.stringify(value ?? (valueType === 'array' ? [] : {}), null, 2)
  }
  if (valueType === 'bool') return value ? 'true' : 'false'
  return value == null ? '' : String(value)
}

function parseValue(raw, valueType) {
  if (valueType === 'int') return Number.parseInt(raw || '0', 10)
  if (valueType === 'float') return Number.parseFloat(raw || '0')
  if (valueType === 'bool') return raw === true || raw === 'true'
  if (valueType === 'json' || valueType === 'array') return JSON.parse(raw || (valueType === 'array' ? '[]' : '{}'))
  return raw == null ? '' : String(raw)
}

function parseJsonField(raw, fallback, label) {
  try {
    return JSON.parse(raw || fallback)
  } catch {
    throw new Error(`${label} JSON 格式无效`)
  }
}

function buildFormPayload(form) {
  const validationSchema = parseJsonField(form.validation_schema, '{}', '校验规则')
  return {
    category: form.category,
    config_key: form.config_key.trim(),
    config_name: form.config_name.trim(),
    value_type: form.value_type,
    value:
      form.value_type === 'json' || form.value_type === 'array'
        ? parseJsonField(form.value, form.value_type === 'array' ? '[]' : '{}', '当前值')
        : parseValue(form.value, form.value_type),
    default_value:
      form.value_type === 'json' || form.value_type === 'array'
        ? parseJsonField(form.default_value, form.value_type === 'array' ? '[]' : '{}', '默认值')
        : parseValue(form.default_value, form.value_type),
    description: form.description,
    validation_schema: validationSchema,
    is_active: form.is_active,
    is_public: form.is_public,
    is_sensitive: form.is_sensitive,
    requires_restart: form.requires_restart,
    change_reason: form.change_reason,
  }
}

function ConfigForm({ categories, form, setForm, saving, onSubmit, onCancel }) {
  const isJsonLike = form.value_type === 'json' || form.value_type === 'array'
  const controlClass = 'sf-control w-full'

  return (
    <div className="glass-card rounded-2xl p-5 space-y-4 border border-gold-500/20">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="space-y-1">
          <span className="text-xs text-navy-400">分类</span>
          <select className={controlClass} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            <option value="">请选择分类</option>
            {categories.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name}（{item.code}）
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-xs text-navy-400">配置键</span>
          <input className={controlClass} value={form.config_key} onChange={(e) => setForm({ ...form, config_key: e.target.value })} placeholder="creation.max_outline_chars" />
        </label>
        <label className="space-y-1">
          <span className="text-xs text-navy-400">配置名称</span>
          <input className={controlClass} value={form.config_name} onChange={(e) => setForm({ ...form, config_name: e.target.value })} placeholder="大纲最大字数" />
        </label>
        <label className="space-y-1">
          <span className="text-xs text-navy-400">值类型</span>
          <select
            className={controlClass}
            value={form.value_type}
            onChange={(e) => setForm({ ...form, value_type: e.target.value, value: '', default_value: '' })}
          >
            {VALUE_TYPES.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="space-y-1">
          <span className="text-xs text-navy-400">当前值</span>
          {form.value_type === 'bool' ? (
            <select className={controlClass} value={String(form.value)} onChange={(e) => setForm({ ...form, value: e.target.value })}>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : isJsonLike ? (
            <textarea className={`${controlClass} min-h-[140px] font-mono`} value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
          ) : (
            <input className={controlClass} type={form.value_type === 'string' ? 'text' : 'number'} value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
          )}
        </label>
        <label className="space-y-1">
          <span className="text-xs text-navy-400">默认值</span>
          {form.value_type === 'bool' ? (
            <select className={controlClass} value={String(form.default_value)} onChange={(e) => setForm({ ...form, default_value: e.target.value })}>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : isJsonLike ? (
            <textarea className={`${controlClass} min-h-[140px] font-mono`} value={form.default_value} onChange={(e) => setForm({ ...form, default_value: e.target.value })} />
          ) : (
            <input className={controlClass} type={form.value_type === 'string' ? 'text' : 'number'} value={form.default_value} onChange={(e) => setForm({ ...form, default_value: e.target.value })} />
          )}
        </label>
      </div>

      <label className="space-y-1 block">
        <span className="text-xs text-navy-400">校验规则 JSON</span>
        <textarea className={`${controlClass} min-h-[90px] font-mono`} value={form.validation_schema} onChange={(e) => setForm({ ...form, validation_schema: e.target.value })} />
      </label>

      <label className="space-y-1 block">
        <span className="text-xs text-navy-400">备注</span>
        <textarea className={`${controlClass} min-h-[70px]`} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </label>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-navy-200">
        {[
          ['is_active', '启用'],
          ['is_public', '公开读取'],
          ['is_sensitive', '敏感配置'],
          ['requires_restart', '需要重启'],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center gap-2 rounded-xl bg-navy-900/55 border border-navy-700/40 px-3 py-2">
            <input type="checkbox" checked={Boolean(form[key])} onChange={(e) => setForm({ ...form, [key]: e.target.checked })} />
            {label}
          </label>
        ))}
      </div>

      <label className="space-y-1 block">
        <span className="text-xs text-navy-400">变更原因</span>
        <input className={controlClass} value={form.change_reason} onChange={(e) => setForm({ ...form, change_reason: e.target.value })} placeholder="说明本次调整原因" />
      </label>

      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-200 text-sm">取消</button>
        <button type="button" onClick={onSubmit} disabled={saving} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold disabled:opacity-60">
          <Save className={ICON.md} />
          {saving ? '保存中…' : '保存配置'}
        </button>
      </div>
    </div>
  )
}

export default function SystemConfigCenterPage() {
  const refreshPublicConfigs = useConfigStore((state) => state.fetchPublicConfigs)
  const [categories, setCategories] = useState([])
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [isActive, setIsActive] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [form, setForm] = useState(null)
  const [confirm, setConfirm] = useState(null)

  const loadCategories = useCallback(async () => {
    const data = await admin.listSystemConfigCategories()
    setCategories(data || [])
  }, [])

  const loadConfigs = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: 10,
        keyword: keyword.trim() || undefined,
        category: category || undefined,
        is_active: isActive || undefined,
      }
      const res = await admin.listSystemConfigs(params)
      setItems(res.items)
      setPagination(res.pagination)
    } catch (error) {
      setMessage({ type: 'error', text: error.message || '加载配置失败' })
    } finally {
      setLoading(false)
    }
  }, [page, keyword, category, isActive])

  useEffect(() => {
    loadCategories().catch((error) => setMessage({ type: 'error', text: error.message || '加载分类失败' }))
  }, [loadCategories])

  useEffect(() => {
    loadConfigs()
  }, [loadConfigs])

  const stats = useMemo(() => [
    { label: '配置项', value: pagination?.total ?? items.length, hint: '当前筛选结果' },
    { label: '分类', value: categories.length, hint: '系统配置分类' },
    { label: '公开配置', value: items.filter((item) => item.is_public).length, hint: '当前页公开项' },
    { label: '需重启', value: items.filter((item) => item.requires_restart).length, hint: '当前页高风险项' },
  ], [categories.length, items, pagination?.total])

  function openCreate() {
    setForm({ ...EMPTY_FORM, category: categories[0]?.code || '' })
  }

  function openEdit(row) {
    setForm({
      ...EMPTY_FORM,
      id: row.id,
      category: row.category,
      config_key: row.config_key,
      config_name: row.config_name,
      value_type: row.value_type,
      value: stringifyValue(row.value, row.value_type),
      default_value: stringifyValue(row.default_value, row.value_type),
      description: row.description || '',
      validation_schema: JSON.stringify(row.validation_schema || {}, null, 2),
      is_active: row.is_active,
      is_public: row.is_public,
      is_sensitive: row.is_sensitive,
      requires_restart: row.requires_restart,
      change_reason: '',
    })
  }

  async function saveForm() {
    if (saving) return
    setSaving(true)
    try {
      const payload = buildFormPayload(form)
      if (form.id) {
        await admin.updateSystemConfig(form.id, payload)
      } else {
        await admin.createSystemConfig(payload)
      }
      setMessage({ type: 'success', text: '配置已保存' })
      setForm(null)
      await Promise.all([loadConfigs(), loadCategories(), refreshPublicConfigs({ force: true })])
    } catch (error) {
      setMessage({ type: 'error', text: error.message || '保存失败，请检查 JSON 和类型' })
    } finally {
      setSaving(false)
    }
  }

  async function toggleRow(row) {
    try {
      await admin.toggleSystemConfig(row.id, { change_reason: '后台快速切换状态' })
      setMessage({ type: 'success', text: '配置状态已更新' })
      await Promise.all([loadConfigs(), refreshPublicConfigs({ force: true })])
    } catch (error) {
      setMessage({ type: 'error', text: error.message || '状态更新失败' })
    }
  }

  async function deleteRow() {
    if (!confirm) return
    setSaving(true)
    try {
      await admin.deleteSystemConfig(confirm.id, { change_reason: '后台删除配置' })
      setMessage({ type: 'success', text: '配置已删除' })
      setConfirm(null)
      await Promise.all([loadConfigs(), refreshPublicConfigs({ force: true })])
    } catch (error) {
      setMessage({ type: 'error', text: error.message || '删除失败' })
    } finally {
      setSaving(false)
    }
  }

  async function refreshCache() {
    try {
      await admin.refreshSystemConfigCache()
      await refreshPublicConfigs({ force: true })
      setMessage({ type: 'success', text: '配置缓存已刷新' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message || '刷新缓存失败' })
    }
  }

  const columns = [
    {
      key: 'config',
      title: '配置项',
      render: (row) => (
        <div>
          <div className="font-semibold text-white">{row.config_name}</div>
          <code className="text-xs text-navy-500">{row.config_key}</code>
          <p className="text-xs text-navy-400 mt-1 line-clamp-2">{row.description || '—'}</p>
        </div>
      ),
    },
    { key: 'category', title: '分类', render: (row) => <AdminBadge>{row.category_name || row.category}</AdminBadge> },
    { key: 'value_type', title: '类型', render: (row) => VALUE_TYPES.find((item) => item.value === row.value_type)?.label || row.value_type },
    {
      key: 'flags',
      title: '状态',
      render: (row) => (
        <div className="flex flex-wrap gap-1.5">
          <AdminBadge tone={row.is_active ? 'success' : 'default'}>{row.is_active ? '启用' : '禁用'}</AdminBadge>
          {row.is_public ? <AdminBadge tone="info">公开</AdminBadge> : null}
          {row.is_sensitive ? <AdminBadge tone="warning">敏感</AdminBadge> : null}
          {row.requires_restart ? <AdminBadge tone="danger">需重启</AdminBadge> : null}
        </div>
      ),
    },
    { key: 'updated_at', title: '更新', render: (row) => formatDateTime(row.updated_at) },
    {
      key: 'actions',
      title: '操作',
      render: (row) => (
        <div className="flex gap-2">
          <button type="button" className="text-gold-400 hover:text-gold-300" onClick={() => openEdit(row)}>编辑</button>
          <button type="button" className="text-navy-300 hover:text-white" onClick={() => toggleRow(row)}>
            {row.is_active ? <ToggleRight className={ICON.md} /> : <ToggleLeft className={ICON.md} />}
          </button>
          <button type="button" className="text-danger-400 hover:text-danger-300" onClick={() => setConfirm(row)}>
            <Trash2 className={ICON.md} />
          </button>
        </div>
      ),
    },
  ]

  return (
    <AdminShell
      title="动态配置"
      description="数据库驱动的业务配置中心，支持在线调整、缓存刷新与灰度迁移"
      actions={
        <>
          <button type="button" onClick={refreshCache} className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-navy-800/70 text-navy-200 text-sm">
            <RefreshCw className={ICON.md} />
            刷新缓存
          </button>
          <button type="button" onClick={openCreate} className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold">
            <Plus className={ICON.md} />
            新增配置
          </button>
        </>
      }
    >
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      <AdminStatGrid items={stats} columns={4} />
      <AdminToolbar>
        <AdminSearchInput value={keyword} onChange={(value) => { setKeyword(value); setPage(1) }} placeholder="搜索配置键、名称或备注" />
        <select className="sf-control" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }}>
          <option value="">全部分类</option>
          {categories.map((item) => (
            <option key={item.code} value={item.code}>{item.name}</option>
          ))}
        </select>
        <select className="sf-control" value={isActive} onChange={(e) => { setIsActive(e.target.value); setPage(1) }}>
          <option value="">全部状态</option>
          <option value="true">启用</option>
          <option value="false">禁用</option>
        </select>
      </AdminToolbar>

      {form ? (
        <ConfigForm categories={categories} form={form} setForm={setForm} saving={saving} onSubmit={saveForm} onCancel={() => setForm(null)} />
      ) : null}

      {loading ? (
        <AdminLoading label="配置加载中…" />
      ) : (
        <>
          <AdminTable columns={columns} rows={items} emptyText="暂无配置项" />
          {pagination ? (
            <AdminPagination
              page={pagination.page || page}
              totalPages={pagination.total_pages || 1}
              total={pagination.total || 0}
              onPageChange={setPage}
            />
          ) : null}
        </>
      )}

      <AdminConfirmDialog
        open={Boolean(confirm)}
        title="删除配置"
        message={`确认删除「${confirm?.config_name || ''}」？该操作会禁用并软删除配置，可通过审计日志追踪。`}
        confirmText="删除"
        loading={saving}
        onConfirm={deleteRow}
        onCancel={() => setConfirm(null)}
      />
    </AdminShell>
  )
}

import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { BookOpen, Plus, Save, Search, Trash2 } from 'lucide-react'
import { admin } from '@/services/api'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'
import { HOOK_TYPE_OPTIONS } from '@/constants/portalContent'

function mapAdminHook(h) {
  const typeLabel = HOOK_TYPE_OPTIONS.find((o) => o.value === h.hook_type)?.label || h.hook_type
  const content = h.content || ''
  return {
    id: h.id,
    preview: content.length > 56 ? `${content.slice(0, 56)}…` : content || '（空内容）',
    category: typeLabel,
    hook_type: h.hook_type || 'opening',
    content,
    usage_count: h.use_count || 0,
    is_active: h.is_active !== false,
  }
}

const EMPTY_HOOK_FORM = {
  hook_type: 'opening',
  content: '',
  is_active: true,
}

export default function HookLibraryPanel({ onMessage, embedded = false }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [hooks, setHooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [form, setForm] = useState(EMPTY_HOOK_FORM)

  async function loadHooks() {
    setLoading(true)
    try {
      const data = await admin.getHooks()
      setHooks((Array.isArray(data) ? data : []).map(mapAdminHook))
    } catch (err) {
      onMessage(err.message || '加载钩子库失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHooks()
  }, [])

  const categories = ['all', ...HOOK_TYPE_OPTIONS.map((o) => o.label)]
  const filteredHooks = hooks.filter((h) => {
    const matchType = category === 'all' || h.category === category
    const q = search.trim()
    const matchSearch =
      q === '' || h.content.includes(q) || h.category.includes(q) || h.preview.includes(q)
    return matchType && matchSearch
  })
  const [selectedHookId, setSelectedHookId] = useAdminSelection(filteredHooks, (hook) => hook.id)
  const activeCount = hooks.filter((h) => h.is_active).length

  useEffect(() => {
    if (isCreating) return
    const hook = filteredHooks.find((item) => item.id === selectedHookId)
    if (hook) {
      setForm({
        id: hook.id,
        hook_type: hook.hook_type,
        content: hook.content,
        is_active: hook.is_active,
      })
    }
  }, [selectedHookId, filteredHooks, isCreating])

  function startCreate() {
    setIsCreating(true)
    setForm({ ...EMPTY_HOOK_FORM })
  }

  function cancelCreate() {
    setIsCreating(false)
    const hook = filteredHooks.find((item) => item.id === selectedHookId)
    if (hook) {
      setForm({
        id: hook.id,
        hook_type: hook.hook_type,
        content: hook.content,
        is_active: hook.is_active,
      })
    }
  }

  async function save() {
    if (!form.content?.trim()) {
      onMessage('请填写钩子正文', 'error')
      return
    }
    setSaving(true)
    try {
      if (isCreating) {
        await admin.addHook({
          content: form.content.trim(),
          hook_type: form.hook_type,
          is_active: form.is_active !== false,
        })
        onMessage('模板已创建')
        setIsCreating(false)
      } else {
        await admin.updateHook(form.id, {
          content: form.content.trim(),
          hook_type: form.hook_type,
          is_active: form.is_active !== false,
        })
        onMessage('模板已保存')
      }
      await loadHooks()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function removeHook(id) {
    if (!window.confirm('确定删除该模板？删除后创作主链将不再引用。')) return
    try {
      await admin.deleteHook(id)
      onMessage('已删除')
      setIsCreating(false)
      await loadHooks()
    } catch (err) {
      onMessage(err.message || '删除失败', 'error')
    }
  }

  if (loading) {
    return <div className="text-center py-16 text-navy-400">加载钩子库…</div>
  }

  const detailPanel = isCreating ? (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-navy-200 mb-2">钩子类型</label>
        <select
          value={form.hook_type}
          onChange={(e) => setForm({ ...form, hook_type: e.target.value })}
          className="sf-control sm:w-64"
        >
          {HOOK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-navy-200 mb-2">正文内容</label>
        <textarea
          value={form.content}
          onChange={(e) => setForm({ ...form, content: e.target.value })}
          rows={5}
          placeholder="例如：她总以为自己是替身，直到发现遗嘱上写的是她的名字…"
          className="sf-control resize-y leading-relaxed"
        />
        <p className="text-xs text-navy-400 mt-2">
          可用占位符：{'{role}'}、{'{name}'} 等，生成时由 AI 替换。
        </p>
      </div>
      <label className="flex items-center gap-2 text-sm text-navy-300">
        <input
          type="checkbox"
          checked={form.is_active !== false}
          onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          className="rounded border-white/20"
        />
        启用（仅启用的模板会被创作主链引用）
      </label>
      <div className="flex flex-wrap gap-2 pt-2">
        <button
          type="button"
          disabled={saving}
          onClick={save}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '创建模板'}
        </button>
        <button
          type="button"
          onClick={cancelCreate}
          className="px-4 py-2.5 rounded-xl text-sm text-navy-300 border border-white/10 hover:bg-white/[0.06]"
        >
          取消
        </button>
      </div>
    </div>
  ) : selectedHookId && form.id ? (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-gold-500/15 text-gold-300 border border-gold-500/25">
          {HOOK_TYPE_OPTIONS.find((o) => o.value === form.hook_type)?.label || form.hook_type}
        </span>
        {form.is_active === false && (
          <span className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-white/[0.05] text-slate-400">
            已停用
          </span>
        )}
        {form.id && (
          <span className="text-xs text-navy-400 ml-auto">
            已被引用 {hooks.find((h) => h.id === form.id)?.usage_count?.toLocaleString() || 0} 次
          </span>
        )}
      </div>
      <div>
        <label className="block text-sm font-medium text-navy-200 mb-2">钩子类型</label>
        <select
          value={form.hook_type}
          onChange={(e) => setForm({ ...form, hook_type: e.target.value })}
          className="sf-control sm:w-64"
        >
          {HOOK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-navy-200 mb-2">正文内容</label>
        <textarea
          value={form.content || ''}
          onChange={(e) => setForm({ ...form, content: e.target.value })}
          rows={6}
          className="sf-control resize-y leading-relaxed"
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-navy-300">
        <input
          type="checkbox"
          checked={form.is_active !== false}
          onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          className="rounded border-white/20"
        />
        启用
      </label>
      <div className="flex flex-wrap gap-2 pt-2">
        <button
          type="button"
          disabled={saving}
          onClick={save}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '保存修改'}
        </button>
        <button
          type="button"
          onClick={() => removeHook(form.id)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-red-400 border border-red-500/30 hover:bg-red-500/10"
        >
          <Trash2 className="w-4 h-4" />
          删除
        </button>
      </div>
    </div>
  ) : null

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      {!embedded ? (
        <div className="sf-console-panel p-5 border border-blue-500/15 bg-blue-500/5">
          <p className="text-sm text-navy-200 leading-relaxed">
            <span className="text-white font-medium">钩子库</span>
            存放短剧「开场 / 反转 / 悬念」等可复用短句。用户走创作主链时，系统从这里随机抽取
            <strong className="text-gold-300">已启用</strong>
            的模板注入生成，用户不会在创作表单里看到这些文案。
          </p>
        </div>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {HOOK_TYPE_OPTIONS.map((opt) => (
          <div
            key={opt.value}
            className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2"
          >
            <p className="text-xs font-medium text-white">{opt.label}</p>
            <p className="text-[10px] text-navy-400 mt-0.5 leading-snug">{opt.hint}</p>
          </div>
        ))}
      </div>

      <div className="sf-console-panel p-4 flex flex-col lg:flex-row lg:items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索正文内容…"
            className="sf-control pl-12"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="sf-control min-w-[140px]"
        >
          <option value="all">全部类型</option>
          {HOOK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.label}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="text-xs text-navy-400 whitespace-nowrap">
          共 {hooks.length} 条 · {activeCount} 条启用
        </div>
        <button
          type="button"
          onClick={startCreate}
          className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold shrink-0"
        >
          <Plus className="w-4 h-4" />
          新建模板
        </button>
      </div>

      {filteredHooks.length === 0 && !isCreating ? (
        <div className="sf-console-panel p-12 text-center text-navy-400">
          <BookOpen className="w-12 h-12 mx-auto mb-3 text-navy-400" />
          <p className="text-white font-medium mb-1">暂无匹配的模板</p>
          <p className="text-sm mb-4">调整搜索或类型筛选，或新建第一条模板</p>
          <button
            type="button"
            onClick={startCreate}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold"
          >
            <Plus className="w-4 h-4" />
            新建模板
          </button>
        </div>
      ) : (
        <AdminMasterDetail
          listTitle="模板列表"
          listHint="点击一条，在右侧编辑正文与类型"
          detailTitle={isCreating ? '新建模板' : '编辑模板'}
          detailHint={
            isCreating
              ? '填写正文并选择类型，保存后立即可供创作主链引用'
              : '修改后点保存，仅影响之后的新创作'
          }
          items={filteredHooks}
          selectedId={isCreating ? null : selectedHookId}
          showDetail={isCreating || (!!selectedHookId && !!form.id)}
          onSelect={(id) => {
            setIsCreating(false)
            setSelectedHookId(id)
          }}
          getId={(hook) => hook.id}
          sidebarWidthClass="lg:grid-cols-[minmax(260px,320px)_minmax(0,1fr)]"
          renderListItem={(hook, { active, onSelect }) => (
            <AdminMasterDetailListButton
              key={hook.id}
              active={active && !isCreating}
              onClick={onSelect}
              title={hook.preview}
              subtitle={hook.category}
              meta={
                !hook.is_active
                  ? '已停用'
                  : hook.usage_count > 0
                    ? `引用 ${hook.usage_count} 次`
                    : undefined
              }
            />
          )}
          renderDetail={() => detailPanel}
          emptyDetail="← 从左侧选择模板，或点「新建模板」"
        />
      )}
    </motion.div>
  )
}

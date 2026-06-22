import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Archive, Check, Plus, RefreshCw, Save, Upload } from 'lucide-react'
import { admin } from '@/services/api'
import {
  AdminWorkbench,
  adminBtnPrimary,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'
import { cn } from '@/utils/cn'

export const TIER_TABS = [
  { key: '1', label: 'Tier1 铁律' },
  { key: '2', label: 'Tier2 题材' },
  { key: '3', label: 'Tier3 节点' },
  { key: '4', label: 'Tier4 合规' },
  { key: 'draft', label: '待审核' },
]

const STATUS_LABEL = {
  active: '已生效',
  draft: '待审核',
  archived: '已归档',
}

const EMPTY_FORM = {
  title: '',
  body: '',
  note: '',
  priority: 100,
  rule_key: '',
  section: 'custom',
}

export default function SkillRulesPanel({ onMessage }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tier') || '1'
  const filterSection = searchParams.get('section') || ''
  const filterQ = searchParams.get('q') || ''

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [flattening, setFlattening] = useState(false)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [summary, setSummary] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [isNew, setIsNew] = useState(false)

  const selected = items.find((item) => item.id === selectedId)

  const queryParams = useMemo(() => {
    if (tab === 'draft') return { status: 'draft', page_size: 200 }
    const base = { tier: tab, status: 'active', page_size: 200 }
    if (tab === '2') return { ...base, scope_type: 'genre' }
    if (tab === '3') return { ...base, scope_type: 'node' }
    return base
  }, [tab])

  function switchTier(key) {
    const next = new URLSearchParams(searchParams)
    next.set('tier', key)
    next.delete('section')
    setSearchParams(next, { replace: true })
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await admin.listSkillRuleItems({
        ...queryParams,
        section: filterSection || undefined,
        q: filterQ || undefined,
      })
      const list = data.items || []
      setItems(list)
      setTotal(data.total ?? list.length)
      setSummary(data.summary || null)
      if (list.length && !list.some((i) => i.id === selectedId)) {
        setSelectedId(list[0].id)
        setIsNew(false)
      }
      if (!list.length) {
        setSelectedId(null)
        setIsNew(false)
      }
    } catch (err) {
      onMessage(err.message || '加载规则条目失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [queryParams, filterSection, filterQ, onMessage])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (selected && !isNew) {
      setForm({
        title: selected.title || '',
        body: selected.body || '',
        note: selected.note || '',
        priority: selected.priority ?? 100,
        rule_key: selected.rule_key || '',
        section: selected.section || '',
      })
    }
  }, [selected?.id, isNew])

  function handleNew() {
    setIsNew(true)
    setSelectedId('__new__')
    setForm({
      ...EMPTY_FORM,
      section: filterSection || 'custom',
      rule_key: `t${tab}.global.custom.${Date.now()}`,
    })
  }

  async function saveItem() {
    if (!form.title.trim() || !form.body.trim()) {
      onMessage('标题与正文不能为空', 'error')
      return
    }
    setSaving(true)
    try {
      if (isNew) {
        await admin.createSkillRuleItem({
          tier: Number(tab === 'draft' ? 1 : tab),
          scope_type: tab === '2' ? 'genre' : tab === '3' ? 'node' : 'global',
          scope_key: '',
          section: form.section,
          rule_key: form.rule_key,
          title: form.title,
          body: form.body,
          note: form.note,
          priority: Number(form.priority) || 100,
          status: tab === 'draft' ? 'draft' : 'active',
        })
        onMessage('规则条目已创建')
      } else if (selected) {
        await admin.updateSkillRuleItem(selected.id, {
          ...selected,
          title: form.title,
          body: form.body,
          note: form.note,
          priority: Number(form.priority) || 100,
        })
        onMessage('规则条目已保存')
      }
      setIsNew(false)
      await load()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function approveItem() {
    if (!selected) return
    try {
      await admin.approveSkillRuleItem(selected.id)
      onMessage('规则条目已批准生效')
      await load()
    } catch (err) {
      onMessage(err.message || '批准失败', 'error')
    }
  }

  async function archiveItem() {
    if (!selected) return
    try {
      await admin.archiveSkillRuleItem(selected.id)
      onMessage('规则条目已归档')
      await load()
    } catch (err) {
      onMessage(err.message || '归档失败', 'error')
    }
  }

  async function importRules() {
    setImporting(true)
    try {
      const data = await admin.importSkillRules({ overwrite: true })
      onMessage(`导入完成：${JSON.stringify(data?.counts || {})} · 拆分 ${data?.flatten?.created ?? 0} 条`)
      await load()
    } catch (err) {
      onMessage(err.message || '导入失败', 'error')
    } finally {
      setImporting(false)
    }
  }

  async function flattenRules() {
    setFlattening(true)
    try {
      const data = await admin.flattenSkillRuleItems({ overwrite: true })
      onMessage(`拆分完成：新增 ${data?.created ?? 0} 条，跳过 ${data?.skipped ?? 0} 条`)
      await load()
    } catch (err) {
      onMessage(err.message || '拆分失败', 'error')
    } finally {
      setFlattening(false)
    }
  }

  const sectionOptions = useMemo(() => {
    const set = new Set(items.map((i) => i.section).filter(Boolean))
    return Array.from(set).sort()
  }, [items])

  const toolbar = (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {TIER_TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => switchTier(t.key)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm border transition',
                tab === t.key
                  ? 'bg-gold-400/20 text-gold-300 border-gold-400/30'
                  : 'border-white/10 bg-white/[0.03] text-navy-300 hover:text-white',
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={handleNew} className={adminBtnPrimary()}>
            <Plus className="w-4 h-4" />
            新增条目
          </button>
          <button type="button" disabled={importing} onClick={importRules} className={adminBtnSecondary()}>
            <Upload className="w-4 h-4" />
            {importing ? '导入中…' : '从磁盘导入'}
          </button>
          <button type="button" disabled={flattening} onClick={flattenRules} className={adminBtnSecondary()}>
            <RefreshCw className={`w-4 h-4 ${flattening ? 'animate-spin' : ''}`} />
            {flattening ? '拆分中…' : '重新拆分'}
          </button>
          <button type="button" onClick={load} className={adminBtnSecondary()}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs">
        <input
          className="sf-control text-sm min-w-[180px]"
          placeholder="搜索标题 / 正文 / rule_key"
          value={filterQ}
          onChange={(e) => {
            const next = new URLSearchParams(searchParams)
            if (e.target.value) next.set('q', e.target.value)
            else next.delete('q')
            setSearchParams(next, { replace: true })
          }}
        />
        <select
          className="sf-control text-sm min-w-[140px]"
          value={filterSection}
          onChange={(e) => {
            const next = new URLSearchParams(searchParams)
            if (e.target.value) next.set('section', e.target.value)
            else next.delete('section')
            setSearchParams(next, { replace: true })
          }}
        >
          <option value="">全部分区</option>
          {sectionOptions.map((sec) => (
            <option key={sec} value={sec}>
              {sec}
            </option>
          ))}
        </select>
        <span className="text-navy-500">
          共 {total} 条
          {summary?.total_apply_count != null ? ` · 累计引用 ${summary.total_apply_count}` : ''}
        </span>
      </div>
    </div>
  )

  const listEmpty = (
    <div className="text-center space-y-3 max-w-md">
      <p className="text-sm text-navy-300">当前分类下暂无规则条目</p>
      <p className="text-xs text-navy-500 leading-relaxed">
        请先「从磁盘导入」配置包，系统会自动拆分为逐条记录；也可点击「新增条目」手动创建。
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        <button type="button" disabled={importing} onClick={importRules} className={adminBtnSecondary()}>
          从磁盘导入
        </button>
        <button type="button" disabled={flattening} onClick={flattenRules} className={adminBtnSecondary()}>
          重新拆分
        </button>
      </div>
    </div>
  )

  return (
    <AdminWorkbench
      listTitle="规则条目"
      toolbar={toolbar}
      listItems={items}
      selectedId={isNew ? '__new__' : selectedId}
      onSelect={(id) => {
        setIsNew(false)
        setSelectedId(id)
      }}
      getItemId={(item) => item.id}
      listLoading={loading}
      listEmpty={listEmpty}
      renderListItem={(item, { active, onSelect }) => (
        <button
          key={item.id}
          type="button"
          onClick={onSelect}
          className={cn(
            'w-full rounded-xl px-3 py-2.5 text-left border transition',
            active ? 'border-gold-500/35 bg-gold-400/10' : 'border-transparent hover:bg-white/[0.06]',
          )}
        >
          <div className="text-sm font-medium text-white truncate">{item.title}</div>
          <div className="text-[10px] text-navy-400 truncate mt-0.5 font-mono">{item.rule_key}</div>
          <div className="flex items-center gap-2 mt-1 text-[10px] text-navy-500">
            <span>{item.section_label || item.section}</span>
            <span>·</span>
            <span>{STATUS_LABEL[item.status] || item.status}</span>
            <span className="ml-auto text-gold-400/80">{item.apply_count ?? 0} 次引用</span>
          </div>
        </button>
      )}
      detailEmpty="从左侧选择规则条目，或点击「新增条目」"
    >
      {(selected || isNew) ? (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-white">{isNew ? '新增规则条目' : form.title}</h3>
            {!isNew && selected ? (
              <>
                <p className="text-xs font-mono text-navy-400 mt-1">{selected.rule_key}</p>
                <p className="text-sm text-navy-400 mt-2">
                  Tier {selected.tier} · {selected.scope_type}/{selected.scope_key || 'global'} · {selected.section}
                </p>
                <p className="text-xs text-gold-400/90 mt-1">
                  已被渲染引用 {selected.apply_count ?? 0} 次
                  {selected.last_applied_at ? ` · 最近 ${selected.last_applied_at}` : ''}
                </p>
              </>
            ) : null}
          </div>

          {isNew ? (
            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">rule_key</span>
              <input
                className="sf-control font-mono text-xs"
                value={form.rule_key}
                onChange={(e) => setForm((f) => ({ ...f, rule_key: e.target.value }))}
              />
            </label>
          ) : null}

          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">标题</span>
            <input
              className="sf-control"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>

          <label className="block">
            <span className="text-xs text-navy-400 mb-1 block">规则正文（注入 Prompt）</span>
            <textarea
              rows={14}
              className="sf-control w-full text-sm leading-relaxed"
              value={form.body}
              onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
              spellCheck={false}
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">优先级</span>
              <input
                type="number"
                className="sf-control"
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              />
            </label>
            <label className="block">
              <span className="text-xs text-navy-400 mb-1 block">备注</span>
              <input
                className="sf-control"
                value={form.note}
                onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={saveItem}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm"
            >
              <Save className="w-4 h-4" />
              {saving ? '保存中…' : '保存'}
            </button>
            {!isNew && selected?.status === 'draft' ? (
              <button
                type="button"
                onClick={approveItem}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm"
              >
                <Check className="w-4 h-4" />
                批准生效
              </button>
            ) : null}
            {!isNew && selected?.status !== 'archived' ? (
              <button type="button" onClick={archiveItem} className={adminBtnSecondary()}>
                <Archive className="w-4 h-4" />
                归档
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </AdminWorkbench>
  )
}

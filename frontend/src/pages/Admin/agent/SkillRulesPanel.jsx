import { useEffect, useMemo, useState } from 'react'
import { Check, Archive, RefreshCw, Save, Upload } from 'lucide-react'
import { admin } from '@/services/api'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'

const TIER_TABS = [
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

export default function SkillRulesPanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [tab, setTab] = useState('1')
  const [items, setItems] = useState([])
  const [selectedId, setSelectedId] = useAdminSelection(items, (item) => item.id)
  const [editJson, setEditJson] = useState('')
  const [editNote, setEditNote] = useState('')

  const selected = items.find((item) => item.id === selectedId)

  const queryParams = useMemo(() => {
    if (tab === 'draft') return { status: 'draft' }
    const base = { tier: tab, status: 'active' }
    if (tab === '2') return { ...base, scope_type: 'genre' }
    if (tab === '3') return { ...base, scope_type: 'node' }
    return base
  }, [tab])

  async function load() {
    setLoading(true)
    try {
      const data = await admin.listSkillRules(queryParams)
      const list = data.items
      setItems(list)
      if (list.length && !list.find((i) => i.id === selectedId)) {
        setSelectedId(list[0].id)
      }
    } catch (err) {
      onMessage(err.message || '加载技能规则失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [tab])

  useEffect(() => {
    if (selected) {
      setEditJson(JSON.stringify(selected.content || {}, null, 2))
      setEditNote(selected.note || '')
    }
  }, [selected?.id])

  async function saveRule() {
    if (!selected) return
    let content
    try {
      content = JSON.parse(editJson)
    } catch {
      onMessage('JSON 格式无效', 'error')
      return
    }
    setSaving(true)
    try {
      await admin.updateSkillRule(selected.id, {
        tier: selected.tier,
        scope_type: selected.scope_type,
        scope_key: selected.scope_key,
        section: selected.section,
        content,
        version_tag: selected.version_tag,
        status: selected.status,
        note: editNote,
      })
      onMessage('规则已保存')
      await load()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function approveRule() {
    if (!selected) return
    try {
      await admin.approveSkillRule(selected.id)
      onMessage('规则已批准生效')
      await load()
    } catch (err) {
      onMessage(err.message || '批准失败', 'error')
    }
  }

  async function archiveRule() {
    if (!selected) return
    try {
      await admin.archiveSkillRule(selected.id)
      onMessage('规则已归档')
      await load()
    } catch (err) {
      onMessage(err.message || '归档失败', 'error')
    }
  }

  async function importRules() {
    setImporting(true)
    try {
      const data = await admin.importSkillRules({ overwrite: true })
      onMessage(`导入完成：${JSON.stringify(data?.counts || {})}`)
      await load()
    } catch (err) {
      onMessage(err.message || '导入失败', 'error')
    } finally {
      setImporting(false)
    }
  }

  if (loading && !items.length) {
    return <div className="text-center py-16 text-navy-400">加载技能规则…</div>
  }

  return (
    <div className="space-y-4 pb-24">
      <div className="glass-card rounded-2xl p-5 border border-emerald-500/15 bg-emerald-500/5">
        <h2 className="text-lg font-bold text-white mb-1">技能规则库</h2>
        <p className="text-sm text-navy-300">
          Tier1–4 规则 DB 优先，磁盘 skill-rules JSON 兜底。批准后同 scope 旧 active 自动归档。
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TIER_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              tab === t.key
                ? 'bg-gold-400/20 text-gold-300 border border-gold-400/30'
                : 'bg-navy-800/50 text-navy-300 border border-navy-700/40'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <AdminMasterDetail
        listTitle="规则列表"
        items={items}
        selectedId={selectedId}
        onSelect={setSelectedId}
        getId={(item) => item.id}
        sidebarWidthClass="lg:grid-cols-[300px_minmax(0,1fr)]"
        emptyList={
          <div className="px-3 py-6 text-sm text-navy-400 space-y-3">
            <p>当前分类暂无已生效规则。</p>
            <p className="text-xs text-navy-500 leading-relaxed">
              首次使用请点击右下角「从磁盘导入」，将 demo4book 下 tier1–4 JSON 写入数据库。
            </p>
            <button
              type="button"
              disabled={importing}
              onClick={importRules}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-gold-400/15 text-gold-300 text-xs border border-gold-400/25"
            >
              <Upload className="w-3.5 h-3.5" />
              {importing ? '导入中…' : '从磁盘导入'}
            </button>
          </div>
        }
        renderListItem={(item, { active, onSelect }) => (
          <AdminMasterDetailListButton
            key={item.id}
            active={active}
            onClick={onSelect}
            title={item.content?.label || item.scope_key || item.section || 'global'}
            subtitle={`T${item.tier} · ${STATUS_LABEL[item.status] || item.status}`}
          />
        )}
        renderDetail={(item) =>
          item ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{item.label || item.section}</h3>
                <p className="text-xs text-navy-500 font-mono mt-1">{item.id}</p>
                <p className="text-sm text-navy-400 mt-2">
                  Tier {item.tier} · {item.scope_type}/{item.scope_key || 'global'} · {item.section}
                </p>
              </div>
              <label className="block">
                <span className="text-xs text-navy-400 mb-1 block">备注</span>
                <input
                  value={editNote}
                  onChange={(e) => setEditNote(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm"
                />
              </label>
              <textarea
                rows={20}
                value={editJson}
                onChange={(e) => setEditJson(e.target.value)}
                className="w-full font-mono text-xs px-4 py-3 rounded-2xl bg-navy-950 border border-navy-700/40 text-navy-100"
                spellCheck={false}
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={saving}
                  onClick={saveRule}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm"
                >
                  <Save className="w-4 h-4" />
                  保存
                </button>
                {item.status === 'draft' ? (
                  <button
                    type="button"
                    onClick={approveRule}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm"
                  >
                    <Check className="w-4 h-4" />
                    批准生效
                  </button>
                ) : null}
                {item.status !== 'archived' ? (
                  <button
                    type="button"
                    onClick={archiveRule}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-navy-800/70 text-navy-200 text-sm"
                  >
                    <Archive className="w-4 h-4" />
                    归档
                  </button>
                ) : null}
              </div>
            </div>
          ) : (
            <p className="text-navy-500">请选择一条规则</p>
          )
        }
      />

      <div className="fixed bottom-0 left-0 right-0 md:left-64 z-30 px-6 py-4 bg-navy-950/90 border-t border-navy-800/60 backdrop-blur-md flex justify-end gap-3">
        <button
          type="button"
          disabled={importing}
          onClick={importRules}
          className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-100 text-sm flex items-center gap-2"
        >
          <Upload className="w-4 h-4" />
          {importing ? '导入中…' : '从磁盘导入'}
        </button>
        <button
          type="button"
          onClick={load}
          className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-100 text-sm flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>
    </div>
  )
}

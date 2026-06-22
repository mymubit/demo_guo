import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, RefreshCw, Search } from 'lucide-react'
import AiConfigShell from '@/components/admin/ai-config/AiConfigShell'
import { AdminMessage } from '@/components/admin/AdminUI'
import {
  AdminLifecycleBadge,
  AdminWorkbench,
  adminBtnPrimary,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'
import { adminSkill } from '@/services/admin/skill'
import SkillDetailPanel from './SkillDetailPanel'
import {
  EMPTY_SKILL_FORM,
  LAYER_OPTIONS,
  mapSkillToForm,
  buildSkillPayload,
  STATUS_FILTER_TABS,
  SKILL_DETAIL_TABS,
} from './skillFormUtils'

export default function SkillCenterPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const detailTab = searchParams.get('tab') || 'overview'

  useEffect(() => {
    if (searchParams.get('tab') === 'rules') {
      navigate('/admin/tier-rules', { replace: true })
    }
  }, [searchParams, navigate])

  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const [selected, setSelected] = useState(null)
  const [isNew, setIsNew] = useState(false)
  const [form, setForm] = useState(EMPTY_SKILL_FORM)
  const [saving, setSaving] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [filterLayer, setFilterLayer] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterQ, setFilterQ] = useState('')
  const [page, setPage] = useState(1)
  const [skillStats, setSkillStats] = useState(null)
  const [skillVersions, setSkillVersions] = useState([])
  const [publishTarget, setPublishTarget] = useState(null)
  const [grayWeight, setGrayWeight] = useState(100)

  const showMsg = useCallback((text, type = 'success') => {
    setMessage({ type, text })
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await adminSkill.listDefinitions({
        skill_layer: filterLayer || undefined,
        lifecycle_status: filterStatus || undefined,
        q: filterQ || undefined,
        page,
        page_size: 20,
      })
      setItems(data.items || [])
      setTotal(data.total ?? data.pagination?.total ?? data.items?.length ?? 0)
    } catch (err) {
      showMsg(err.message || '加载失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [filterLayer, filterStatus, filterQ, page, showMsg])

  useEffect(() => { setPage(1) }, [filterLayer, filterStatus, filterQ])
  useEffect(() => { load() }, [load])

  async function loadSkillMeta(item) {
    if (!item?.id) {
      setSkillStats(null)
      setSkillVersions([])
      return
    }
    try {
      const [statsRes, versionsRes] = await Promise.all([
        adminSkill.getDefinitionStats({ days: 7 }),
        adminSkill.listDefinitionVersions(item.id),
      ])
      const statsRow = (statsRes?.items || []).find((row) => row.skill_id === item.skill_id)
      setSkillStats(statsRow || null)
      setSkillVersions(versionsRes?.items || versionsRes || [])
    } catch {
      setSkillStats(null)
      setSkillVersions([])
    }
  }

  async function handleSelect(id) {
    const item = items.find((row) => row.id === id)
    if (!item) return
    setSelectedId(id)
    setSelected(item)
    setIsNew(false)
    setDetailLoading(true)
    setForm(EMPTY_SKILL_FORM)
    loadSkillMeta(item)
    try {
      const detail = await adminSkill.getDefinition(item.id)
      const merged = { ...item, ...(detail || {}) }
      setSelected(merged)
      setForm(mapSkillToForm(merged))
    } catch (err) {
      showMsg(err.message || '加载技能详情失败', 'error')
      setForm(mapSkillToForm(item))
    } finally {
      setDetailLoading(false)
    }
  }

  function handleNew() {
    setSelectedId(null)
    setSelected(null)
    setIsNew(true)
    setForm(EMPTY_SKILL_FORM)
    setSkillStats(null)
    setSkillVersions([])
    setSearchParams({ tab: 'overview' }, { replace: true })
  }

  function setDetailTab(key) {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    setSearchParams(next, { replace: true })
  }

  async function handleSave() {
    setSaving(true)
    try {
      const payload = buildSkillPayload(form)
      if (selected?.id) {
        await adminSkill.updateDefinition(selected.id, payload)
        showMsg('技能已更新')
        await load()
        await handleSelect(selected.id)
      } else {
        await adminSkill.createDefinition(payload)
        showMsg('技能已创建')
        setIsNew(false)
        await load()
      }
    } catch (err) {
      showMsg(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handlePublishConfirm() {
    if (!publishTarget) return
    try {
      await adminSkill.publishDefinition(publishTarget.id, { gray_weight: grayWeight })
      showMsg(`技能已${grayWeight < 100 ? '灰度' : '全量'}发布`)
      setPublishTarget(null)
      await load()
      if (selectedId) await handleSelect(selectedId)
    } catch (err) {
      showMsg(err.message || '发布失败', 'error')
    }
  }

  async function handleRollback() {
    if (!selected || !confirm(`确定回滚「${selected.skill_id}」到上一版本？`)) return
    try {
      await adminSkill.rollbackDefinition(selected.id)
      showMsg('已回滚')
      await load()
      await handleSelect(selected.id)
    } catch (err) {
      showMsg(err.message || '回滚失败', 'error')
    }
  }

  async function handleDelete() {
    if (!selected || !confirm(`确定废弃技能「${selected.skill_id}」？`)) return
    try {
      await adminSkill.deleteDefinition(selected.id)
      showMsg('技能已废弃')
      setSelectedId(null)
      setSelected(null)
      setIsNew(false)
      await load()
    } catch (err) {
      showMsg(err.message || '删除失败', 'error')
    }
  }

  const listToolbar = (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[160px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-500" />
          <input
            className="sf-control pl-9 w-full text-sm"
            placeholder="搜索 skill_id / 名称…"
            value={filterQ}
            onChange={(e) => setFilterQ(e.target.value)}
          />
        </div>
        <button type="button" onClick={load} className={adminBtnSecondary()} title="刷新">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
        <button type="button" onClick={handleNew} className={adminBtnPrimary()}>
          <Plus className="h-4 w-4" />
          新增
        </button>
      </div>
      <select className="sf-control text-sm w-full" value={filterLayer} onChange={(e) => setFilterLayer(e.target.value)}>
        {LAYER_OPTIONS.map((o) => (
          <option key={o.value || 'all'} value={o.value}>{o.label}</option>
        ))}
      </select>
      <div className="flex flex-wrap gap-1.5">
        {STATUS_FILTER_TABS.map((tab) => (
          <button
            key={tab.value || 'all'}
            type="button"
            onClick={() => setFilterStatus(tab.value)}
            className={`px-2.5 py-1 text-xs rounded-full border transition ${
              filterStatus === tab.value
                ? 'border-gold-500/40 bg-gold-400/15 text-gold-200'
                : 'border-white/10 text-navy-400 hover:text-navy-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <p className="text-xs text-navy-500">共 {total} 个技能</p>
    </div>
  )

  return (
    <AiConfigShell sectionId="skills">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminWorkbench
        toolbar={listToolbar}
        listItems={items}
        selectedId={isNew ? '__new__' : selectedId}
        onSelect={handleSelect}
        getItemId={(item) => item.id}
        listLoading={loading}
        listEmpty={<p className="px-3 py-8 text-sm text-navy-400 text-center">暂无技能</p>}
        renderListItem={(item, { active, onSelect }) => (
          <button
            key={item.id}
            type="button"
            onClick={onSelect}
            className={`w-full rounded-xl px-3 py-2.5 text-left border transition ${
              active ? 'border-gold-500/35 bg-gold-400/10' : 'border-transparent hover:bg-white/[0.06]'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="font-medium text-sm text-white truncate">{item.name || item.skill_id}</div>
                <div className="text-xs font-mono text-navy-400 truncate mt-0.5">{item.skill_id}</div>
              </div>
              <AdminLifecycleBadge status={item.lifecycle_status} grayWeight={item.gray_weight} />
            </div>
            <div className="mt-1.5 flex items-center gap-2 text-[10px] text-navy-500">
              <span>{item.skill_layer_label || item.skill_layer || '—'}</span>
              <span className="ml-auto">v{item.version}</span>
            </div>
          </button>
        )}
        listFooter={
          <div className="border-t border-white/5 p-2 flex items-center justify-between text-xs text-navy-500">
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="disabled:opacity-40">上一页</button>
            <span>第 {page} 页</span>
            <button type="button" disabled={items.length < 20} onClick={() => setPage((p) => p + 1)} className="disabled:opacity-40">下一页</button>
          </div>
        }
        detailTabs={selected || isNew ? SKILL_DETAIL_TABS : null}
        activeTab={detailTab}
        onTabChange={setDetailTab}
        detailLoading={detailLoading && !isNew}
        detailEmpty="从左侧选择技能，或点击「新增」"
      >
        {(selected || isNew) ? (
          <SkillDetailPanel
            selected={selected}
            form={form}
            setForm={setForm}
            detailTab={detailTab}
            skillStats={skillStats}
            skillVersions={skillVersions}
            isNew={isNew}
            saving={saving}
            onSave={handleSave}
            onPublish={() => { setPublishTarget(selected); setGrayWeight(100) }}
            onRollback={handleRollback}
            onDelete={handleDelete}
            onMessage={showMsg}
          />
        ) : null}
      </AdminWorkbench>

      {publishTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="sf-console-panel p-6 w-full max-w-sm shadow-modal">
            <h3 className="text-lg font-semibold text-white mb-1">发布技能</h3>
            <p className="text-sm text-navy-400 mb-4 font-mono">{publishTarget.skill_id}</p>
            <label className="block text-xs text-navy-400 mb-1">灰度权重（%）</label>
            <input type="range" min={0} max={100} step={10} value={grayWeight} onChange={(e) => setGrayWeight(Number(e.target.value))} className="w-full mb-2" />
            <div className="flex justify-between text-xs text-navy-500 mb-4">
              <span>0%</span>
              <span className="text-gold-300 font-medium">{grayWeight}%</span>
              <span>100%</span>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => setPublishTarget(null)} className={adminBtnSecondary()}>取消</button>
              <button type="button" onClick={handlePublishConfirm} className={adminBtnPrimary()}>确认发布</button>
            </div>
          </div>
        </div>
      ) : null}
    </AiConfigShell>
  )
}

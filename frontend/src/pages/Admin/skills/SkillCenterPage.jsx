import { useEffect, useState, useCallback } from 'react'
import {
  Plus, Search, RefreshCw, Upload, ChevronDown,
  CheckCircle, Clock, AlertTriangle, XCircle,
} from 'lucide-react'
import { adminSkill } from '@/services/admin/skill'

const LAYER_OPTIONS = [
  { value: '', label: '全部层级' },
  { value: 'foundation', label: '基础能力层' },
  { value: 'business',   label: '业务技能层' },
  { value: 'tool',       label: '工具能力层' },
]

const STATUS_TABS = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '上线' },
  { value: 'gray', label: '灰度' },
  { value: 'deprecated', label: '废弃' },
]

const STATUS_BADGE = {
  draft:      { label: '草稿',   cls: 'bg-gray-100 text-gray-600' },
  active:     { label: '上线',   cls: 'bg-green-100 text-green-700' },
  gray:       { label: '灰度',   cls: 'bg-yellow-100 text-yellow-700' },
  deprecated: { label: '废弃',   cls: 'bg-red-100 text-red-600' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_BADGE[status] || { label: status, cls: 'bg-gray-100 text-gray-500' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

function GrayWeightBadge({ weight }) {
  if (weight === 100) return null
  return (
    <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-orange-100 text-orange-700">
      灰度 {weight}%
    </span>
  )
}

const EMPTY_FORM = {
  skill_id: '', name: '', version: '1.0.0',
  skill_layer: '', sub_category: '',
  system_hint: '', content: '',
  input_schema: '{}', output_schema: '{}',
  timeout_seconds: 60, quota_cost: 0, fallback_skill_id: '',
  retry_policy: '{"max_attempts": 2, "backoff_seconds": 5}',
}

export default function SkillCenterPage() {
  const [items, setItems]           = useState([])
  const [total, setTotal]           = useState(0)
  const [loading, setLoading]       = useState(false)
  const [selected, setSelected]     = useState(null)
  const [showForm, setShowForm]     = useState(false)
  const [form, setForm]             = useState(EMPTY_FORM)
  const [saving, setSaving]         = useState(false)
  const [toast, setToast]           = useState(null)

  // 筛选条件
  const [filterLayer,  setFilterLayer]  = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterQ,      setFilterQ]      = useState('')
  const [page,         setPage]         = useState(1)
  const [skillStats,   setSkillStats]   = useState(null)
  const [skillVersions,setSkillVersions]= useState([])

  // 发布灰度弹窗
  const [publishTarget, setPublishTarget]   = useState(null)
  const [grayWeight,    setGrayWeight]      = useState(100)

  const showMsg = useCallback((msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await adminSkill.listDefinitions({
        skill_layer:      filterLayer || undefined,
        lifecycle_status: filterStatus || undefined,
        q:                filterQ || undefined,
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

  // 选中技能同步到表单
  function handleSelect(item) {
    setSelected(item)
    loadSkillMeta(item)
    setForm({
      skill_id:          item.skill_id,
      name:              item.name,
      version:           item.version,
      skill_layer:       item.skill_layer || '',
      sub_category:      item.sub_category || '',
      system_hint:       item.system_hint || '',
      content:           item.content || '',
      input_schema:      JSON.stringify(item.input_schema || {}, null, 2),
      output_schema:     JSON.stringify(item.output_schema || {}, null, 2),
      timeout_seconds:   item.timeout_seconds ?? 60,
      quota_cost:        item.quota_cost ?? 0,
      fallback_skill_id: item.fallback_skill_id || '',
      retry_policy:      JSON.stringify(item.retry_policy || {}, null, 2),
    })
    setShowForm(true)
  }

  function handleNew() {
    setSelected(null)
    setForm(EMPTY_FORM)
    setShowForm(true)
  }

  async function handleSave() {
    setSaving(true)
    try {
      const payload = {
        ...form,
        input_schema:  JSON.parse(form.input_schema  || '{}'),
        output_schema: JSON.parse(form.output_schema || '{}'),
        retry_policy:  JSON.parse(form.retry_policy  || '{}'),
        timeout_seconds: Number(form.timeout_seconds),
        quota_cost:      Number(form.quota_cost),
      }
      if (selected) {
        await adminSkill.updateDefinition(selected.id, payload)
        showMsg('技能已更新')
      } else {
        await adminSkill.createDefinition(payload)
        showMsg('技能已创建')
      }
      setShowForm(false)
      load()
    } catch (err) {
      showMsg(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handlePublish() {
    if (!publishTarget) return
    try {
      await adminSkill.publishDefinition(publishTarget.id, { gray_weight: grayWeight })
      showMsg(`技能已${grayWeight < 100 ? '灰度' : '全量'}发布`)
      setPublishTarget(null)
      load()
    } catch (err) {
      showMsg(err.message || '发布失败', 'error')
    }
  }

  async function handleDeprecate(item) {
    if (!confirm(`确定废弃技能「${item.skill_id}」？此操作不可逆。`)) return
    try {
      await adminSkill.deprecateDefinition(item.id)
      showMsg('技能已废弃')
      load()
    } catch (err) {
      showMsg(err.message || '操作失败', 'error')
    }
  }

  async function handleRollback(item) {
    if (!confirm(`确定回滚技能「${item.skill_id}」到上一版本？`)) return
    try {
      await adminSkill.rollbackDefinition(item.id)
      showMsg('已回滚到上一版本')
      load()
    } catch (err) {
      showMsg(err.message || '回滚失败', 'error')
    }
  }

  async function handleDelete(item) {
    if (!confirm(`确定废弃并停用技能「${item.skill_id}」？`)) return
    try {
      await adminSkill.deleteDefinition(item.id)
      showMsg('技能已废弃')
      setShowForm(false)
      setSelected(null)
      load()
    } catch (err) {
      showMsg(err.message || '删除失败', 'error')
    }
  }

  return (
    <div className="flex h-full gap-4">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded shadow-lg text-sm text-white
          ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* 左侧：列表 */}
      <div className="w-80 flex-shrink-0 flex flex-col border border-gray-200 rounded-lg overflow-hidden bg-white">
        {/* 工具栏 */}
        <div className="p-3 border-b border-gray-100 space-y-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
              <input
                className="w-full pl-7 pr-2 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
                placeholder="搜索 skill_id / 名称…"
                value={filterQ}
                onChange={(e) => setFilterQ(e.target.value)}
              />
            </div>
            <button
              onClick={load}
              className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleNew}
              className="flex items-center gap-1 px-2.5 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
            >
              <Plus className="w-3.5 h-3.5" />
              新增
            </button>
          </div>
          <select
            className="w-full text-xs border border-gray-200 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
            value={filterLayer}
            onChange={(e) => setFilterLayer(e.target.value)}
          >
            {LAYER_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <div className="flex flex-wrap gap-1.5">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value || 'all'}
                type="button"
                onClick={() => setFilterStatus(tab.value)}
                className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                  filterStatus === tab.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="text-xs text-gray-400">共 {total} 个技能</div>
        </div>

        {/* 技能列表 */}
        <div className="flex-1 overflow-y-auto">
          {items.length === 0 && !loading && (
            <div className="p-8 text-center text-gray-400 text-sm">暂无技能</div>
          )}
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelect(item)}
              className={`w-full text-left px-3 py-2.5 border-b border-gray-100 hover:bg-blue-50 transition-colors
                ${selected?.id === item.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''}`}
            >
              <div className="flex items-start justify-between gap-1">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-800 truncate">{item.name}</div>
                  <div className="text-xs text-gray-400 truncate mt-0.5">{item.skill_id}</div>
                </div>
                <div className="flex-shrink-0 flex flex-col items-end gap-1">
                  <StatusBadge status={item.lifecycle_status} />
                  <GrayWeightBadge weight={item.gray_weight} />
                </div>
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
                <span>{item.skill_layer_label || item.skill_layer || '—'}</span>
                {item.sub_category && <span>· {item.sub_category}</span>}
                <span className="ml-auto">v{item.version}</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {item.lifecycle_status !== 'deprecated' ? (
                  <>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setPublishTarget(item); setGrayWeight(100) }}
                      className="text-[10px] px-2 py-0.5 rounded bg-green-600 text-white hover:bg-green-700"
                    >
                      发布
                    </button>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDeprecate(item) }}
                      className="text-[10px] px-2 py-0.5 rounded border border-red-200 text-red-500 hover:bg-red-50"
                    >
                      废弃
                    </button>
                  </>
                ) : null}
              </div>
            </button>
          ))}
        </div>
        <div className="border-t border-gray-100 p-2 flex items-center justify-between text-xs text-gray-500">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="disabled:opacity-40"
          >
            上一页
          </button>
          <span>第 {page} 页</span>
          <button
            type="button"
            disabled={items.length < 20}
            onClick={() => setPage((p) => p + 1)}
            className="disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      </div>

      {/* 右侧：编辑区 */}
      {showForm ? (
        <div className="flex-1 flex flex-col border border-gray-200 rounded-lg overflow-hidden bg-white">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">
              {selected ? `编辑：${selected.skill_id}` : '新增技能'}
            </h2>
            {selected && (
              <div className="flex items-center gap-2">
                <StatusBadge status={selected.lifecycle_status} />
                {selected.lifecycle_status !== 'deprecated' && (
                  <>
                    <button
                      onClick={() => { setPublishTarget(selected); setGrayWeight(100) }}
                      className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      发布/灰度
                    </button>
                    <button
                      onClick={() => handleRollback(selected)}
                      className="text-xs px-2 py-1 border border-gray-300 text-gray-600 rounded hover:bg-gray-50"
                    >
                      回滚
                    </button>
                    <button
                      onClick={() => handleDelete(selected)}
                      className="text-xs px-2 py-1 border border-red-200 text-red-500 rounded hover:bg-red-50"
                    >
                      删除
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* 基础信息 */}
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">基础信息</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="技能 ID *" disabled={!!selected}>
                  <input value={form.skill_id} onChange={(e) => setForm({ ...form, skill_id: e.target.value })}
                    disabled={!!selected} className="field-input" placeholder="如 brief.character_extract" />
                </Field>
                <Field label="技能名称 *">
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="field-input" placeholder="如 人物编剧" />
                </Field>
                <Field label="版本号">
                  <input value={form.version} onChange={(e) => setForm({ ...form, version: e.target.value })}
                    className="field-input" placeholder="1.0.0" />
                </Field>
                <Field label="技能层级">
                  <select value={form.skill_layer} onChange={(e) => setForm({ ...form, skill_layer: e.target.value })}
                    className="field-input">
                    <option value="">未分类</option>
                    <option value="foundation">基础能力层</option>
                    <option value="business">业务技能层</option>
                    <option value="tool">工具能力层</option>
                  </select>
                </Field>
                <Field label="子分类">
                  <input value={form.sub_category} onChange={(e) => setForm({ ...form, sub_category: e.target.value })}
                    className="field-input" placeholder="如 人设 / 大纲 / 剧本" />
                </Field>
                <Field label="超时（秒）">
                  <input type="number" value={form.timeout_seconds}
                    onChange={(e) => setForm({ ...form, timeout_seconds: e.target.value })}
                    className="field-input" min={5} max={600} />
                </Field>
                <Field label="配额消耗">
                  <input type="number" value={form.quota_cost}
                    onChange={(e) => setForm({ ...form, quota_cost: e.target.value })}
                    className="field-input" min={0} step={0.1} />
                </Field>
                <Field label="降级技能 ID">
                  <input value={form.fallback_skill_id}
                    onChange={(e) => setForm({ ...form, fallback_skill_id: e.target.value })}
                    className="field-input" placeholder="主技能失败时的降级 skill_id" />
                </Field>
              </div>
            </section>

            {/* System Hint */}
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                System Hint（LLM 系统提示词）
              </h3>
              <textarea
                value={form.system_hint}
                onChange={(e) => setForm({ ...form, system_hint: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                rows={8}
                placeholder="你是短剧结构策划师。根据 projectBrief…"
              />
            </section>

            {/* Schema */}
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                入参 / 出参 Schema（JSONSchema）
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="入参 Schema">
                  <textarea
                    value={form.input_schema}
                    onChange={(e) => setForm({ ...form, input_schema: e.target.value })}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                    rows={6}
                  />
                </Field>
                <Field label="出参 Schema">
                  <textarea
                    value={form.output_schema}
                    onChange={(e) => setForm({ ...form, output_schema: e.target.value })}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                    rows={6}
                  />
                </Field>
              </div>
            </section>

            {/* 重试策略 */}
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">重试策略（JSON）</h3>
              <textarea
                value={form.retry_policy}
                onChange={(e) => setForm({ ...form, retry_policy: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                rows={3}
              />
            </section>

            {/* 调用统计与版本历史 */}
            {selected && (
              <section className="grid gap-3 md:grid-cols-2">
                <div className="rounded border border-gray-100 p-3 text-xs text-gray-600">
                  <h3 className="mb-2 font-semibold text-gray-700">近 7 日调用统计</h3>
                  {skillStats ? (
                    <ul className="space-y-1">
                      <li>调用量：{skillStats.total_calls ?? 0}</li>
                      <li>成功率：{((skillStats.success_rate ?? 0) * 100).toFixed(1)}%</li>
                      <li>开放缺陷：{skillStats.open_defects ?? 0}</li>
                      <li>
                        平均耗时：
                        {skillStats.avg_duration_ms != null
                          ? `${skillStats.avg_duration_ms} ms`
                          : '—'}
                      </li>
                    </ul>
                  ) : (
                    <p>暂无统计数据</p>
                  )}
                </div>
                <div className="rounded border border-gray-100 p-3 text-xs text-gray-600">
                  <h3 className="mb-2 font-semibold text-gray-700">版本历史</h3>
                  {skillVersions.length > 0 ? (
                    <ul className="max-h-28 space-y-1 overflow-y-auto">
                      {skillVersions.map((ver) => (
                        <li key={ver.id}>
                          v{ver.version} · {ver.lifecycle_status_label || ver.lifecycle_status}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>暂无其他版本</p>
                  )}
                </div>
              </section>
            )}

            {/* 技能内容（Markdown） */}
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">技能内容（Markdown）</h3>
              <textarea
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                rows={6}
                placeholder="原始 SKILL.md 完整内容…"
              />
            </section>
          </div>

          <div className="px-4 py-3 border-t border-gray-100 flex justify-end gap-2">
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-sm border border-gray-200 rounded hover:bg-gray-50"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? '保存中…' : '保存'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400 text-sm border border-dashed border-gray-200 rounded-lg">
          从左侧选择技能进行编辑，或点击「新增」创建
        </div>
      )}

      {/* 发布/灰度弹窗 */}
      {publishTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="font-semibold text-gray-800 mb-1">发布技能</h3>
            <p className="text-sm text-gray-500 mb-4">{publishTarget.skill_id}</p>

            <label className="block text-xs text-gray-600 mb-1">灰度权重（%）</label>
            <input
              type="range" min={0} max={100} step={10}
              value={grayWeight}
              onChange={(e) => setGrayWeight(Number(e.target.value))}
              className="w-full mb-1"
            />
            <div className="flex justify-between text-xs text-gray-400 mb-4">
              <span>0%（不生效）</span>
              <span className="font-medium text-blue-600">{grayWeight}%</span>
              <span>100%（全量）</span>
            </div>
            <p className="text-xs text-gray-400 mb-4">
              {grayWeight < 100
                ? `灰度模式：约 ${grayWeight}% 的新项目使用此版本`
                : '全量发布：所有新项目使用此版本'}
            </p>

            <div className="flex gap-2 justify-end">
              <button onClick={() => setPublishTarget(null)}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded hover:bg-gray-50">
                取消
              </button>
              <button onClick={handlePublish}
                className="px-4 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700">
                确认发布
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children, disabled }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  )
}

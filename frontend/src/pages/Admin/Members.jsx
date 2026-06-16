import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Copy, Check, Plus, Trash2, Crown, Ticket } from 'lucide-react'
import { admin } from '@/services/api'
import {
  AdminMessage,
  AdminLoading,
  AdminTable,
  AdminBadge,
  AdminTabBar,
  formatDateTime,
} from '@/components/admin/AdminUI'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'
import {
  formatPricePreview,
  isAutoChargePrice,
  syncChargeFromDiscount,
} from '@/utils/adminEconomics'

const PLAN_FIELD_ROWS = [
  ['name', '套餐名称'],
  ['original_price', '划线原价(元)'],
  ['discount_percent', '折扣(%)'],
  ['price', '实付(元)'],
  ['validity_days', '有效期(天)'],
  ['grant_coins', '开通赠送创作币'],
  ['sort_order', '排序'],
]

const MEMBER_ROUTE_TABS = [
  { key: 'plans', label: '会员套餐', icon: Crown },
  { key: 'codes', label: '兑换卡密', icon: Ticket },
]

const PLAN_SECTIONS = [
  { key: 'packages', label: '套餐定价' },
  { key: 'benefits', label: '权益目录' },
  { key: 'compare', label: '权益对比' },
]

function resolvePlanSection(searchParams) {
  const section = searchParams.get('section')
  if (section === 'benefits') return 'benefits'
  if (section === 'compare') return 'compare'
  return 'packages'
}

function slugFeatureKey(label) {
  const base = String(label || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^\w\u4e00-\u9fff-]/g, '')
  return `benefit_${base || 'item'}_${Date.now().toString(36)}`
}

function promoCodeStatus(row) {
  const expired =
    row.is_expired ??
    (row.expires_at ? new Date(row.expires_at).getTime() < Date.now() : false)
  if (row.is_active === false) return { label: '已停用', tone: 'default' }
  if (expired) return { label: '已过期', tone: 'danger' }
  if (row.used_count >= row.max_uses) {
    return { label: row.max_uses === 1 ? '已兑换' : '已用完', tone: 'default' }
  }
  if (row.used_count === 0) return { label: '未使用', tone: 'success' }
  const left = row.max_uses - row.used_count
  return { label: `剩余 ${left} 次`, tone: 'warning' }
}

export default function MembersAdmin({ forcedTab: forcedTabProp }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const routeTab = searchParams.get('tab') === 'codes' ? 'codes' : 'plans'
  const forcedTab = forcedTabProp || routeTab
  const planSection = resolvePlanSection(searchParams)
  const [tab, setTab] = useState(forcedTab)
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [plans, setPlans] = useState([])
  const [codes, setCodes] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [creating, setCreating] = useState(false)
  const [planSaving, setPlanSaving] = useState(false)
  const [form, setForm] = useState({})
  const [selectedPlanId, setSelectedPlanId] = useAdminSelection(plans, (plan) => plan.id)
  const emptyPlan = {
    name: '',
    price: 99,
    original_price: '',
    discount_percent: 100,
    validity_days: 30,
    grant_coins: 500,
    sort_order: 0,
    is_active: true,
    is_recommended: false,
  }

  function planPayload(formData) {
    return {
      name: formData.name,
      price: formData.price,
      original_price: formData.original_price === '' || formData.original_price == null
        ? null
        : formData.original_price,
      discount_percent: formData.discount_percent ?? 100,
      validity_days: formData.validity_days,
      creation_quota: 0,
      grant_coins: formData.grant_coins,
      is_active: formData.is_active,
      is_recommended: formData.is_recommended,
      sort_order: formData.sort_order,
      features: {},
    }
  }
  const [genForm, setGenForm] = useState({ plan_id: '', count: 5, valid_days: 30, max_uses_per_code: 1 })
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(null)
  const [matrixRows, setMatrixRows] = useState([])
  const [matrixSavingId, setMatrixSavingId] = useState(null)

  async function loadPlans() {
    const data = await admin.listPlans()
    setPlans(Array.isArray(data) ? data : [])
    if (data?.length && !genForm.plan_id) {
      setGenForm((f) => ({ ...f, plan_id: data[0].id }))
    }
  }

  async function loadCodes() {
    const data = await admin.listPromoCodes(50)
    setCodes(Array.isArray(data) ? data : [])
  }

  async function loadMatrix() {
    const data = await admin.listFeatureMatrix()
    setMatrixRows(Array.isArray(data) ? data : [])
  }

  useEffect(() => {
    ;(async () => {
      setLoading(true)
      try {
        await Promise.all([loadPlans(), loadCodes()])
      } catch (err) {
        setMessage({ type: 'error', text: err.message || '加载失败' })
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  useEffect(() => {
    setTab(forcedTab)
  }, [forcedTab])

  useEffect(() => {
    if ((tab === 'plans' || forcedTab === 'plans') && planSection !== 'packages') {
      loadMatrix().catch((err) => setMessage({ type: 'error', text: err.message || '加载权益失败' }))
    }
  }, [tab, forcedTab, planSection])

  function switchMemberTab(key) {
    if (key === 'codes') {
      setSearchParams({ tab: 'codes' }, { replace: true })
      return
    }
    const next = new URLSearchParams(searchParams)
    next.delete('tab')
    setSearchParams(next, { replace: true })
  }

  function switchPlanSection(key) {
    if (key === 'packages') {
      setSearchParams({}, { replace: true })
    } else {
      setSearchParams({ section: key }, { replace: true })
    }
  }

  useEffect(() => {
    if (creating) return
    const plan = plans.find((item) => item.id === selectedPlanId)
    if (plan) {
      setEditingId(plan.id)
      const next = { ...plan }
      next.price = Number(
        syncChargeFromDiscount({
          original: next.original_price,
          discountPercent: next.discount_percent,
          manualPrice: next.price,
        })
      )
      setForm(next)
    }
  }, [selectedPlanId, plans, creating])

  function patchPlanForm(key, rawValue) {
    setForm((prev) => {
      const numericKeys = ['price', 'original_price', 'validity_days', 'grant_coins', 'sort_order', 'discount_percent']
      let value = rawValue
      if (numericKeys.includes(key)) {
        value = key === 'original_price' && rawValue === '' ? '' : Number(rawValue)
      }
      const next = { ...prev, [key]: value }
      if (key === 'original_price' || key === 'discount_percent') {
        next.price = Number(
          syncChargeFromDiscount({
            original: next.original_price,
            discountPercent: next.discount_percent,
            manualPrice: next.price,
          })
        )
      }
      return next
    })
  }

  function renderPlanFormFields() {
    const autoCharge = isAutoChargePrice(form.discount_percent, form.original_price)
    const pricePreview = formatPricePreview({
      original: form.original_price,
      discountPercent: form.discount_percent,
      manualPrice: form.price,
    })
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PLAN_FIELD_ROWS.map(([key, label]) => {
          const readOnlyPrice = key === 'price' && autoCharge
          return (
          <label key={key} className="block">
            <span className="text-xs text-navy-400">
              {label}
              {readOnlyPrice ? '（自动计算）' : ''}
            </span>
            <input
              value={form[key] ?? ''}
              readOnly={readOnlyPrice}
              onChange={(e) => patchPlanForm(key, e.target.value)}
              className={`mt-1 sf-control text-white ${
                readOnlyPrice ? 'bg-slate-900/80 cursor-not-allowed text-gold-300' : ''
              }`}
            />
          </label>
          )
        })}
        <label className="flex items-center gap-2 text-sm text-navy-200">
          <input
            type="checkbox"
            checked={!!form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          启用
        </label>
        <label className="flex items-center gap-2 text-sm text-navy-200">
          <input
            type="checkbox"
            checked={!!form.is_recommended}
            onChange={(e) => setForm({ ...form, is_recommended: e.target.checked })}
          />
          推荐
        </label>
        <p className="md:col-span-2 text-[11px] text-navy-400 leading-relaxed">
          填写划线原价与折扣(%)后，实付由系统自动计算（原价×折扣%）；折扣 100 时可手动填写实付价。开通赠送创作币与人民币打折可叠加。
        </p>
        <p className="md:col-span-2 text-xs text-gold-400/90">{pricePreview}</p>
      </div>
    )
  }

  async function addBenefitRow() {
    const label = window.prompt('权益名称', '')
    if (!label?.trim()) return
    try {
      await admin.saveFeatureMatrixItem({
        feature_key: slugFeatureKey(label),
        label: label.trim(),
        member: true,
        free: false,
        is_active: true,
      })
      showOk('权益已添加')
      await loadMatrix()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '添加失败' })
    }
  }

  async function deleteBenefitRow(row) {
    if (!row?.id) {
      setMessage({ type: 'error', text: '内置默认项不可删除，可先保存为自定义后再删' })
      return
    }
    if (!window.confirm(`确定删除权益「${row.label || row.feature_key}」？`)) return
    try {
      await admin.deleteFeatureMatrixItem(row.id)
      showOk('权益已删除')
      await loadMatrix()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '删除失败' })
    }
  }

  function renderBenefitsPanel() {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="text-sm text-navy-400">
            维护会员可享功能清单；所有付费会员权益一致，套餐卡片会自动引用此处 + 各档开通赠币。
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={seedMatrix}
              className="px-4 py-2 rounded-xl text-sm text-navy-200 border border-white/10 hover:bg-white/[0.06]"
            >
              写入默认项
            </button>
            <button
              type="button"
              onClick={addBenefitRow}
              className="inline-flex items-center gap-1 px-4 py-2 rounded-xl text-sm btn-gold"
            >
              <Plus className="w-4 h-4" />
              添加权益
            </button>
          </div>
        </div>
        <AdminTable
          rowKey="feature_key"
          rows={matrixRows}
          emptyText="暂无权益，请添加或写入默认项"
          columns={[
            {
              key: 'label',
              title: '权益名称',
              render: (r) => (
                <input
                  className="sf-control min-w-[180px] px-2 py-1.5 text-sm"
                  value={r.label || ''}
                  onChange={(e) =>
                    setMatrixRows((list) =>
                      list.map((item) =>
                        item.feature_key === r.feature_key ? { ...item, label: e.target.value } : item
                      )
                    )
                  }
                />
              ),
            },
            {
              key: 'source',
              title: '来源',
              render: (r) => (
                <AdminBadge tone={r.source === 'db' ? 'gold' : 'default'}>
                  {r.source === 'db' ? '已入库' : '默认'}
                </AdminBadge>
              ),
            },
            {
              key: 'actions',
              title: '操作',
              render: (r) => (
                <div className="flex gap-3">
                  <button
                    type="button"
                    className="text-gold-400 text-sm hover:underline disabled:opacity-50"
                    disabled={matrixSavingId === r.feature_key}
                    onClick={() => saveMatrixRow(matrixRows.find((i) => i.feature_key === r.feature_key))}
                  >
                    {matrixSavingId === r.feature_key ? '保存中…' : '保存'}
                  </button>
                  <button
                    type="button"
                    className="text-red-400 text-sm hover:underline disabled:opacity-40"
                    disabled={!r.id}
                    onClick={() => deleteBenefitRow(r)}
                  >
                    删除
                  </button>
                </div>
              ),
            },
          ]}
        />
      </div>
    )
  }

  function renderComparePanel() {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="text-sm text-navy-400">
            C 端会员页「普通用户 vs 会员」对比表；勾选决定两侧是否展示该功能。
          </p>
          <button
            type="button"
            onClick={() => switchPlanSection('benefits')}
            className="px-4 py-2 rounded-xl text-sm text-gold-400 border border-gold-500/30"
          >
            管理权益目录
          </button>
        </div>
        <AdminTable
          rowKey="feature_key"
          rows={matrixRows}
          emptyText="暂无权益项"
          columns={[
            { key: 'label', title: '权益名称', render: (r) => r.label || r.feature_key },
            {
              key: 'free',
              title: '普通用户',
              render: (r) => (
                <input
                  type="checkbox"
                  checked={!!r.free}
                  onChange={(e) =>
                    setMatrixRows((list) =>
                      list.map((item) =>
                        item.feature_key === r.feature_key ? { ...item, free: e.target.checked } : item
                      )
                    )
                  }
                />
              ),
            },
            {
              key: 'member',
              title: '会员',
              render: (r) => (
                <input
                  type="checkbox"
                  checked={!!r.member}
                  onChange={(e) =>
                    setMatrixRows((list) =>
                      list.map((item) =>
                        item.feature_key === r.feature_key ? { ...item, member: e.target.checked } : item
                      )
                    )
                  }
                />
              ),
            },
            {
              key: 'member_only',
              title: '仅会员',
              render: (r) => (
                <input
                  type="checkbox"
                  checked={!!r.member_only}
                  onChange={(e) =>
                    setMatrixRows((list) =>
                      list.map((item) =>
                        item.feature_key === r.feature_key
                          ? { ...item, member_only: e.target.checked }
                          : item
                      )
                    )
                  }
                />
              ),
            },
            {
              key: 'coming_soon',
              title: '即将上线',
              render: (r) => (
                <input
                  type="checkbox"
                  checked={!!r.coming_soon}
                  onChange={(e) =>
                    setMatrixRows((list) =>
                      list.map((item) =>
                        item.feature_key === r.feature_key
                          ? { ...item, coming_soon: e.target.checked }
                          : item
                      )
                    )
                  }
                />
              ),
            },
            {
              key: 'actions',
              title: '操作',
              render: (r) => (
                <button
                  type="button"
                  className="text-gold-400 text-sm hover:underline disabled:opacity-50"
                  disabled={matrixSavingId === r.feature_key}
                  onClick={() => saveMatrixRow(matrixRows.find((i) => i.feature_key === r.feature_key))}
                >
                  {matrixSavingId === r.feature_key ? '保存中…' : '保存对比'}
                </button>
              ),
            },
          ]}
        />
      </div>
    )
  }

  async function saveMatrixRow(row) {
    setMatrixSavingId(row.feature_key)
    try {
      if (row.id) {
        await admin.updateFeatureMatrixItem(row.id, row)
      } else {
        await admin.saveFeatureMatrixItem({
          feature_key: row.feature_key,
          label: row.label,
          free: !!row.free,
          member: !!row.member,
          coming_soon: !!row.coming_soon,
          member_only: !!row.member_only,
          is_active: row.is_active !== false,
          sort_order: row.sort_order,
        })
      }
      showOk('权益项已保存')
      await loadMatrix()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '保存失败' })
    } finally {
      setMatrixSavingId(null)
    }
  }

  async function seedMatrix() {
    try {
      await admin.seedFeatureMatrix()
      showOk('已写入默认权益矩阵')
      await loadMatrix()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '同步失败' })
    }
  }

  function showOk(text) {
    setMessage({ type: 'success', text })
    setTimeout(() => setMessage(null), 3000)
  }

  async function savePlan() {
    if (planSaving) return
    if (!String(form.name || '').trim()) {
      setMessage({ type: 'error', text: '请填写套餐名称' })
      return
    }
    setPlanSaving(true)
    try {
      const payload = planPayload(form)
      if (creating) {
        await admin.createPlan(payload)
        setCreating(false)
        showOk('套餐已创建')
      } else {
        await admin.updatePlan(editingId, payload)
        setEditingId(null)
        showOk('套餐已保存')
      }
      loadPlans()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '保存失败' })
    } finally {
      setPlanSaving(false)
    }
  }

  async function handleDeletePlan(id) {
    if (!window.confirm('确定删除此套餐？若已有会员使用将无法删除。')) return
    try {
      await admin.deletePlan(id)
      showOk('套餐已删除')
      loadPlans()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '删除失败' })
    }
  }

  async function handleGenerate() {
    if (!genForm.plan_id) {
      setMessage({ type: 'error', text: '请选择套餐' })
      return
    }
    setGenerating(true)
    try {
      const res = await admin.generatePromo(genForm)
      showOk(`已生成 ${res?.generated_count ?? genForm.count} 个卡密`)
      await loadCodes()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '生成失败' })
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <AdminLoading />

  return (
    <div className="space-y-6">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <p className="text-sm text-navy-400 rounded-xl border border-white/5 bg-slate-900/60 px-4 py-3">
        套餐可同时配置「人民币打折」（划线原价 + 折扣%）与「开通赠送创作币」；二者独立，可叠加。
      </p>

      <div className="flex flex-wrap gap-2 p-1 sf-console-panel w-fit">
        {MEMBER_ROUTE_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => switchMemberTab(t.key)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              forcedTab === t.key
                ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 shadow-lg shadow-gold-500/20'
                : 'text-navy-200 hover:bg-white/[0.06]'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {(tab === 'plans' || forcedTab === 'plans') && (
        <div className="space-y-4">
          <AdminTabBar tabs={PLAN_SECTIONS} active={planSection} onChange={switchPlanSection} />

          {planSection === 'packages' ? (
        <AdminMasterDetail
          listTitle="会员套餐"
          showDetail={creating || selectedPlanId != null}
          listHeader={
            <div className="px-2 pb-2">
              <button
                type="button"
                onClick={() => {
                  setCreating(true)
                  setEditingId(null)
                  setForm({ ...emptyPlan })
                }}
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl btn-gold text-sm"
              >
                <Plus className="w-4 h-4" />
                新建套餐
              </button>
            </div>
          }
          items={plans}
          selectedId={creating ? null : selectedPlanId}
          onSelect={(id) => {
            setCreating(false)
            setSelectedPlanId(id)
          }}
          getId={(plan) => plan.id}
          emptyList={<p className="px-2 py-4 text-sm text-navy-400">暂无套餐，点击上方新建</p>}
          renderListItem={(plan, { active, onSelect }) => (
            <AdminMasterDetailListButton
              key={plan.id}
              active={active && !creating}
              onClick={onSelect}
              title={plan.name}
              subtitle={
                plan.discount_label
                  ? `¥${plan.price}（${plan.discount_label}） / ${plan.validity_days}天`
                  : `¥${plan.price} / ${plan.validity_days}天`
              }
              meta={`${plan.grant_coins ?? 0} 币`}
              badges={plan.is_recommended ? ['推荐'] : []}
            />
          )}
          renderDetail={() =>
            creating ? (
              <div className="space-y-4">
                <h3 className="text-white font-semibold">新建套餐</h3>
                {renderPlanFormFields()}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={savePlan}
                    disabled={planSaving}
                    className="px-5 py-2.5 rounded-xl btn-gold disabled:opacity-60"
                  >
                    {planSaving ? '创建中…' : '创建'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setCreating(false)}
                    className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-navy-200 hover:bg-white/[0.06]"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : editingId ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-lg font-semibold text-white">{form.name || '编辑套餐'}</h3>
                  <button
                    type="button"
                    onClick={() => handleDeletePlan(editingId)}
                    className="px-3 py-2 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 inline-flex items-center gap-1 text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    删除
                  </button>
                </div>
                {renderPlanFormFields()}
                <button
                  type="button"
                  onClick={savePlan}
                  disabled={planSaving}
                  className="px-5 py-2.5 rounded-xl btn-gold disabled:opacity-60"
                >
                  {planSaving ? '保存中…' : '保存当前套餐'}
                </button>
              </div>
            ) : (
              <div className="text-sm text-navy-400">请从左侧选择套餐，或点击「新建套餐」</div>
            )
          }
        />
          ) : planSection === 'benefits' ? (
            renderBenefitsPanel()
          ) : (
            renderComparePanel()
          )}
        </div>
      )}

      {(tab === 'codes' || forcedTab === 'codes') && (
        <div className="space-y-6">
          <div className="sf-console-panel p-5 grid grid-cols-1 md:grid-cols-4 gap-4">
            <label className="block md:col-span-2">
              <span className="text-xs text-navy-400">关联套餐</span>
              <select
                value={genForm.plan_id}
                onChange={(e) => setGenForm({ ...genForm, plan_id: e.target.value })}
                className="mt-1 sf-control"
              >
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-navy-400">生成数量</span>
              <input
                type="number"
                min={1}
                max={500}
                value={genForm.count}
                onChange={(e) => setGenForm({ ...genForm, count: Number(e.target.value) })}
                className="mt-1 sf-control"
              />
            </label>
            <label className="block">
              <span className="text-xs text-navy-400">有效天数</span>
              <input
                type="number"
                min={1}
                value={genForm.valid_days}
                onChange={(e) => setGenForm({ ...genForm, valid_days: Number(e.target.value) })}
                className="mt-1 sf-control"
              />
            </label>
            <button
              type="button"
              disabled={generating}
              onClick={handleGenerate}
              className="md:col-span-4 py-3 rounded-xl btn-gold font-medium disabled:opacity-60"
            >
              {generating ? '生成中…' : '批量生成卡密'}
            </button>
          </div>

          <AdminTable
            rowKey="id"
            rows={codes}
            emptyText="暂无卡密，请先生成"
            columns={[
              {
                key: 'code',
                title: '卡密',
                render: (r) => (
                  <div className="flex items-center gap-2 font-mono text-gold-400">
                    {r.code}
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard?.writeText(r.code)
                        setCopied(r.id)
                        setTimeout(() => setCopied(null), 1500)
                      }}
                      className="text-navy-400 hover:text-white"
                    >
                      {copied === r.id ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                ),
              },
              { key: 'plan_name', title: '套餐', render: (r) => r.plan?.name || r.plan_name || '—' },
              {
                key: 'used',
                title: '状态',
                render: (r) => {
                  const status = promoCodeStatus(r)
                  return <AdminBadge tone={status.tone}>{status.label}</AdminBadge>
                },
              },
              { key: 'expires_at', title: '过期时间', render: (r) => formatDateTime(r.expires_at) },
              { key: 'created_at', title: '创建时间', render: (r) => formatDateTime(r.created_at) },
            ]}
          />
        </div>
      )}
    </div>
  )
}

import { useState, useEffect, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Compass,
  Gauge,
  LayoutList,
  Clock,
  Save,
  SlidersHorizontal,
  Tag,
} from 'lucide-react'
import { admin } from '@/services/api'
import { DEFAULT_SHOW } from '@/utils/creationEntry'
import { ENTRY_ICON_MAP } from '@/utils/creationEntryMeta'
import { AdminTabBar } from '@/components/admin/AdminUI'
import { CREATION_FORM_TAB_HINTS } from '@/constants/portalContent'

export default function CreationFormPanel({ onMessage, embedded = false }) {
  const FORM_SUB_TABS = [
    { key: 'entries', label: '创作入口', icon: Compass },
    { key: 'themes', label: '题材', icon: Tag },
    { key: 'params', label: '项目参数', icon: SlidersHorizontal },
    { key: 'copy', label: '区块标题', icon: LayoutList },
  ]

  const SECTION_TITLE_LABELS = {
    creationEntry: '创作入口区',
    theme: '题材选择',
    budgetLevel: '预算档位',
    targetPlatform: '目标平台',
    episodes: '集数设置',
    formatVariant: '格式变体',
  }

  const SHOW_BLOCKS = [
    { key: 'theme', label: '题材选择' },
    { key: 'coreIdea', label: '一句话 / 原创创意' },
    { key: 'outline', label: '分集大纲' },
    { key: 'novel', label: '小说原文' },
    { key: 'referenceBlock', label: '参考作品', isRef: true },
    { key: 'ipSequel', label: 'IP 续作设置' },
    { key: 'projectParams', label: '项目参数（预算/平台/集数/格式）' },
    { key: 'audience', label: '目标受众' },
  ]

  const FIELD_BLOCKS = [
    { key: 'coreIdea', label: '创意输入区' },
    { key: 'outline', label: '大纲输入区' },
    { key: 'novel', label: '小说输入区' },
    { key: 'reference', label: '参考作品区' },
    { key: 'ipSequel', label: 'IP 约束区' },
  ]

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const subTab = searchParams.get('section') || 'entries'
  const setSubTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('section', key)
    setSearchParams(next, { replace: true })
  }
  const [activeEntry, setActiveEntry] = useState('from-scratch')
  const [skillVersion, setSkillVersion] = useState('')
  const [form, setForm] = useState({
    budgetLevels: [],
    platforms: [],
    creationEntries: [],
    formatVariants: [],
    episodeSettings: {},
    sections: {},
    themes: [],
    creationEntryProfiles: {},
  })

  async function load() {
    setLoading(true)
    try {
      const data = await admin.getCreationFormCatalog()
      const catalog = data?.catalog || data || {}
      setSkillVersion(data?.skillVersion || '')
      setForm({
        budgetLevels: catalog.budgetLevels || [],
        platforms: catalog.platforms || [],
        creationEntries: catalog.creationEntries || [],
        formatVariants: catalog.formatVariants || [],
        episodeSettings: catalog.episodeSettings || {},
        sections: catalog.sections || {},
        themes: catalog.themes || [],
        creationEntryProfiles: catalog.creationEntryProfiles || {},
      })
      const first = catalog.creationEntries?.[0]?.key
      if (first) setActiveEntry(first)
    } catch (err) {
      onMessage(err.message || '加载创作表单配置失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  function patchList(key, index, field, value) {
    setForm((prev) => {
      const list = [...(prev[key] || [])]
      list[index] = { ...list[index], [field]: value }
      return { ...prev, [key]: list }
    })
  }

  function patchEpisode(field, value) {
    setForm((prev) => ({
      ...prev,
      episodeSettings: { ...prev.episodeSettings, [field]: value },
    }))
  }

  function patchSection(sectionKey, field, value) {
    setForm((prev) => ({
      ...prev,
      sections: {
        ...prev.sections,
        [sectionKey]: { ...(prev.sections?.[sectionKey] || {}), [field]: value },
      },
    }))
  }

  function patchTheme(index, field, value) {
    patchList('themes', index, field, value)
  }

  function getCatalogEntry(entryKey) {
    return (form.creationEntries || []).find((e) => e.key === entryKey) || { key: entryKey, name: entryKey }
  }

  function getEntryProfile(entryKey) {
    const cur = form.creationEntryProfiles?.[entryKey] || {}
    const show = cur.show && typeof cur.show === 'object' ? cur.show : {}
    return {
      ...cur,
      pipelineHints: cur.pipelineHints || { prefilledSteps: [], caption: '' },
      validation: cur.validation || { requiredFields: {} },
      show: { ...DEFAULT_SHOW, ...show },
    }
  }

  function patchEntryMeta(entryKey, field, value) {
    const idx = (form.creationEntries || []).findIndex((e) => e.key === entryKey)
    if (idx >= 0) patchList('creationEntries', idx, field, value)
  }

  function patchEntrySteps(entryKey, text) {
    const steps = String(text || '')
      .split(/\n/)
      .map((s) => s.trim())
      .filter(Boolean)
    patchEntryProfile(entryKey, 'steps', steps)
  }

  function patchEntryPipelineHint(entryKey, field, value) {
    setForm((prev) => {
      const cur = prev.creationEntryProfiles?.[entryKey] || {}
      const hints = cur.pipelineHints || {}
      return {
        ...prev,
        creationEntryProfiles: {
          ...prev.creationEntryProfiles,
          [entryKey]: {
            ...cur,
            pipelineHints: { ...hints, [field]: value },
          },
        },
      }
    })
  }

  function patchEntryPrefilledSteps(entryKey, text) {
    const prefilledSteps = String(text || '')
      .split(/[,，\s]+/)
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !Number.isNaN(n))
    patchEntryPipelineHint(entryKey, 'prefilledSteps', prefilledSteps)
  }

  function patchEntryProfile(entryKey, field, value) {
    setForm((prev) => ({
      ...prev,
      creationEntryProfiles: {
        ...prev.creationEntryProfiles,
        [entryKey]: { ...(prev.creationEntryProfiles?.[entryKey] || {}), [field]: value },
      },
    }))
  }

  function patchEntryShow(entryKey, field, value) {
    setForm((prev) => {
      const cur = prev.creationEntryProfiles?.[entryKey] || {}
      return {
        ...prev,
        creationEntryProfiles: {
          ...prev.creationEntryProfiles,
          [entryKey]: { ...cur, show: { ...(cur.show || {}), [field]: value } },
        },
      }
    })
  }

  function patchEntryRequiresAdapt(entryKey, value) {
    patchEntryProfile(entryKey, 'requiresAdapt', value)
  }

  function patchEntryValidationMinLength(entryKey, fieldKey, minLength) {
    setForm((prev) => {
      const cur = prev.creationEntryProfiles?.[entryKey] || {}
      const validation = cur.validation || {}
      const requiredFields = validation.requiredFields || {}
      const nextRequired = { ...requiredFields }
      const nextValue = Number(minLength) || 0
      if (nextValue <= 0) {
        delete nextRequired[fieldKey]
      } else {
        nextRequired[fieldKey] = {
          ...(nextRequired[fieldKey] || {}),
          minLength: nextValue,
        }
      }
      return {
        ...prev,
        creationEntryProfiles: {
          ...prev.creationEntryProfiles,
          [entryKey]: {
            ...cur,
            validation: {
              ...validation,
              requiredFields: nextRequired,
            },
          },
        },
      }
    })
  }

  function patchEntryFieldBlock(entryKey, blockKey, field, value) {
    setForm((prev) => {
      const cur = prev.creationEntryProfiles?.[entryKey] || {}
      return {
        ...prev,
        creationEntryProfiles: {
          ...prev.creationEntryProfiles,
          [entryKey]: {
            ...cur,
            [blockKey]: { ...(cur[blockKey] || {}), [field]: value },
          },
        },
      }
    })
  }

  function entryPreviewChips(entryKey) {
    const show = getEntryProfile(entryKey).show || {}
    const chips = []
    if (show.theme !== false) chips.push('题材')
    if (show.coreIdea) chips.push('创意')
    if (show.outline) chips.push('大纲')
    if (show.novel) chips.push('小说')
    if (show.referenceBlock === 'required') chips.push('参考作品(必填)')
    else if (show.referenceBlock === 'optional') chips.push('参考作品(可选)')
    if (show.ipSequel) chips.push('IP约束')
    if (show.projectParams !== false) chips.push('项目参数')
    if (show.audience) chips.push('受众')
    return chips
  }

  function isFieldBlockVisible(entryKey, blockKey) {
    const show = getEntryProfile(entryKey).show || {}
    if (blockKey === 'coreIdea') return !!show.coreIdea
    if (blockKey === 'outline') return !!show.outline
    if (blockKey === 'novel') return !!show.novel
    if (blockKey === 'reference') return show.referenceBlock && show.referenceBlock !== 'hidden'
    if (blockKey === 'ipSequel') return !!show.ipSequel
    return false
  }

  async function importFromDisk() {
    setImporting(true)
    try {
      await admin.importCreationFormFromDisk({ mode: 'sync' })
      onMessage('已从磁盘同步创作入口 profile')
      await load()
    } catch (err) {
      onMessage(err.message || '磁盘同步失败', 'error')
    } finally {
      setImporting(false)
    }
  }

  async function save() {
    setSaving(true)
    try {
      const presets = String(form.episodeSettings?.presetsText || '')
        .split(/[,，\s]+/)
        .map((n) => parseInt(n, 10))
        .filter((n) => !Number.isNaN(n))
      const episodeSettings = {
        ...form.episodeSettings,
        min: Number(form.episodeSettings.min) || 20,
        max: Number(form.episodeSettings.max) || 200,
        step: Number(form.episodeSettings.step) || 10,
        default: Number(form.episodeSettings.default) || 80,
        durationMinutes: Number(form.episodeSettings.durationMinutes) || 2,
        presets: presets.length ? presets : form.episodeSettings.presets,
      }
      delete episodeSettings.presetsText

      await admin.saveCreationFormCatalog({
        budgetLevels: form.budgetLevels,
        platforms: form.platforms,
        creationEntries: form.creationEntries,
        formatVariants: form.formatVariants,
        episodeSettings,
        sections: form.sections,
        themes: form.themes,
        creationEntryProfiles: form.creationEntryProfiles,
      })
      onMessage('创作表单配置已保存，C 端刷新后生效')
      await load()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const inputCls =
    'w-full px-3 py-2.5 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:border-gold-500/50 outline-none'
  const labelCls = 'text-xs text-navy-400 mb-1 block'

  if (loading) {
    return <div className="text-center py-16 text-navy-400">加载创作表单配置…</div>
  }

  const ep = form.episodeSettings || {}
  const presetsText =
    ep.presetsText ??
    (Array.isArray(ep.presets) ? ep.presets.join(', ') : '20, 40, 60, 80, 100, 120, 150, 200')
  const profile = getEntryProfile(activeEntry)
  const show = profile.show || {}

  return (
    <div className="space-y-5 pb-24">
      {!embedded ? (
        <div className="glass-card rounded-2xl p-5 border border-gold-500/20 bg-gradient-to-r from-gold-500/5 to-transparent">
          <h2 className="text-lg font-bold text-white mb-1">创作页配置</h2>
          <p className="text-sm text-navy-300 leading-relaxed">
            用户在 C 端「发起创作」看到的入口、题材、参数与表单文案，<strong className="text-gold-300">全部存数据库</strong>
            。保存后用户刷新创作页即生效；与主链 Agent 提示词无关。
          </p>
          <p className="text-xs text-navy-500 mt-2">
            主链步骤与扣费请前往
            <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
              主链工作室
            </Link>
          </p>
        </div>
      ) : null}

      <AdminTabBar tabs={FORM_SUB_TABS} active={subTab} onChange={setSubTab} stretch />
      <p className="text-sm text-navy-400">{CREATION_FORM_TAB_HINTS[subTab] || ''}</p>

      {subTab === 'entries' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-4 space-y-2">
            <div className="flex items-center justify-between px-1 mb-2">
              <p className="text-xs text-navy-400">选择要配置的入口（与 C 端顶部 Tab 一致）</p>
              <button
                type="button"
                onClick={importFromDisk}
                disabled={importing}
                className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
              >
                {importing ? '同步中…' : '从磁盘同步 profile'}
              </button>
            </div>
            {(form.creationEntries || []).map((entry) => {
              const active = activeEntry === entry.key
              return (
                <button
                  key={entry.key}
                  type="button"
                  onClick={() => setActiveEntry(entry.key)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all ${
                    active
                      ? 'border-gold-400/50 bg-gold-400/10 ring-1 ring-gold-400/30'
                      : 'border-navy-700/40 bg-navy-800/30 hover:bg-navy-800/50'
                  }`}
                >
                  <div className={`font-semibold ${active ? 'text-gold-300' : 'text-white'}`}>
                    {entry.name || entry.key}
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {entryPreviewChips(entry.key).map((c) => (
                      <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-navy-900/60 text-navy-400">
                        {c}
                      </span>
                    ))}
                  </div>
                </button>
              )
            })}
          </div>

          <div className="lg:col-span-8 glass-card rounded-2xl p-6 space-y-6">
            <div>
              <h3 className="text-white font-semibold text-lg">{getCatalogEntry(activeEntry).name}</h3>
              <p className="text-xs text-navy-500 font-mono mt-0.5">{activeEntry}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="block">
                <span className={labelCls}>C 端入口按钮名称</span>
                <input
                  value={getCatalogEntry(activeEntry).name || ''}
                  onChange={(e) => patchEntryMeta(activeEntry, 'name', e.target.value)}
                  className={inputCls}
                />
              </label>
              <label className="block">
                <span className={labelCls}>入口卡片标签（tag）</span>
                <input
                  value={profile.tag || ''}
                  onChange={(e) => patchEntryProfile(activeEntry, 'tag', e.target.value)}
                  className={inputCls}
                  placeholder="例：原创"
                />
              </label>
              <label className="block">
                <span className={labelCls}>入口标题（headline）</span>
                <input
                  value={profile.headline || ''}
                  onChange={(e) => patchEntryProfile(activeEntry, 'headline', e.target.value)}
                  className={inputCls}
                  placeholder="例：原创短剧"
                />
              </label>
              <label className="block">
                <span className={labelCls}>入口图标（iconKey）</span>
                <select
                  value={profile.iconKey || 'penTool'}
                  onChange={(e) => patchEntryProfile(activeEntry, 'iconKey', e.target.value)}
                  className={inputCls}
                >
                  {Object.keys(ENTRY_ICON_MAP).map((key) => (
                    <option key={key} value={key}>
                      {key}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block md:col-span-2">
                <span className={labelCls}>入口卡片描述（Hub 页展示）</span>
                <textarea
                  rows={2}
                  value={profile.description || ''}
                  onChange={(e) => patchEntryProfile(activeEntry, 'description', e.target.value)}
                  className={`${inputCls} resize-none`}
                  placeholder="例：从一句话创意出发，7 项技能依次产出…"
                />
              </label>
              <label className="block md:col-span-2">
                <span className={labelCls}>切换后顶部说明（用户选此入口时展示）</span>
                <textarea
                  rows={2}
                  value={profile.summary || ''}
                  onChange={(e) => patchEntryProfile(activeEntry, 'summary', e.target.value)}
                  className={`${inputCls} resize-none`}
                  placeholder="例：你已有分集大纲，系统将基于大纲扩写…"
                />
              </label>
              <label className="block md:col-span-2">
                <span className={labelCls}>填写进度步骤（每行一步，最后一项通常为「技能流水线」）</span>
                <textarea
                  rows={4}
                  value={(profile.steps || []).join('\n')}
                  onChange={(e) => patchEntrySteps(activeEntry, e.target.value)}
                  className={`${inputCls} resize-none font-mono text-xs`}
                  placeholder={'选题材\n写创意\n确认简报\n技能流水线'}
                />
              </label>
              <label className="block md:col-span-2">
                <span className={labelCls}>技能链差异说明（表单页流水线区下方）</span>
                <textarea
                  rows={2}
                  value={profile.pipelineHints?.caption || ''}
                  onChange={(e) => patchEntryPipelineHint(activeEntry, 'caption', e.target.value)}
                  className={`${inputCls} resize-none`}
                  placeholder="例：第 1 步由你的大纲预填，从第 2 步结构规划起扩写"
                />
              </label>
              <label className="block">
                <span className={labelCls}>预填步骤序号（逗号分隔，0 表示无）</span>
                <input
                  value={(profile.pipelineHints?.prefilledSteps || []).join(', ')}
                  onChange={(e) => patchEntryPrefilledSteps(activeEntry, e.target.value)}
                  className={inputCls}
                  placeholder="例：1"
                />
              </label>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-3">此入口下 C 端显示哪些区块</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SHOW_BLOCKS.map((block) => {
                  if (block.isRef) {
                    const val = show.referenceBlock || 'optional'
                    return (
                      <div key={block.key} className="p-3 rounded-xl bg-navy-900/40 border border-navy-700/40">
                        <div className="text-sm text-navy-200 mb-2">{block.label}</div>
                        <div className="flex gap-1 flex-wrap">
                          {[
                            { v: 'hidden', l: '不显示' },
                            { v: 'optional', l: '可选' },
                            { v: 'required', l: '必填' },
                          ].map((opt) => (
                            <button
                              key={opt.v}
                              type="button"
                              onClick={() => patchEntryShow(activeEntry, 'referenceBlock', opt.v)}
                              className={`px-2.5 py-1 rounded-lg text-xs ${
                                val === opt.v
                                  ? 'bg-gold-400/20 text-gold-300'
                                  : 'bg-navy-800/60 text-navy-400'
                              }`}
                            >
                              {opt.l}
                            </button>
                          ))}
                        </div>
                      </div>
                    )
                  }
                  const isOn =
                    block.key === 'theme' || block.key === 'projectParams'
                      ? show[block.key] !== false
                      : !!show[block.key]
                  return (
                    <label
                      key={block.key}
                      className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer ${
                        isOn ? 'border-gold-500/30 bg-gold-500/5' : 'border-navy-700/40 bg-navy-900/30'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isOn}
                        onChange={(e) => patchEntryShow(activeEntry, block.key, e.target.checked)}
                        className="rounded"
                      />
                      <span className="text-sm text-navy-100">{block.label}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-navy-700/40 bg-navy-900/30 space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-white">入口执行与校验规则</h4>
                  <p className="text-xs text-navy-500 mt-1">保存后同时影响 C 端前置校验与后端提交校验。</p>
                </div>
                <label className="flex items-center gap-2 text-sm text-navy-200">
                  <input
                    type="checkbox"
                    checked={!!profile.requiresAdapt}
                    onChange={(e) => patchEntryRequiresAdapt(activeEntry, e.target.checked)}
                    className="rounded"
                  />
                  需要 Adapt 预处理
                </label>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { key: 'reference_work', label: '参考作品说明最小字数' },
                  { key: 'outline_text', label: '分集大纲最小字数' },
                  { key: 'novel_text', label: '小说原文最小字数' },
                  { key: 'ip_keep_rules', label: 'IP 约束最小字数' },
                ].map((item) => {
                  const rule = profile.validation?.requiredFields?.[item.key] || {}
                  return (
                    <label key={item.key} className="block">
                      <span className={labelCls}>{item.label}（0 表示使用默认）</span>
                      <input
                        type="number"
                        min="0"
                        value={rule.minLength || 0}
                        onChange={(e) => patchEntryValidationMinLength(activeEntry, item.key, e.target.value)}
                        className={inputCls}
                      />
                    </label>
                  )
                })}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-3">输入区文案（仅已启用的区块）</h4>
              <div className="space-y-4">
                {FIELD_BLOCKS.filter((b) => isFieldBlockVisible(activeEntry, b.key)).map((block) => (
                  <div key={block.key} className="p-4 rounded-xl border border-navy-700/40 bg-navy-900/30 space-y-3">
                    <div className="text-sm font-medium text-gold-400/90">{block.label}</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <label className="block">
                        <span className={labelCls}>标题</span>
                        <input
                          value={profile[block.key]?.title || ''}
                          onChange={(e) => patchEntryFieldBlock(activeEntry, block.key, 'title', e.target.value)}
                          className={inputCls}
                        />
                      </label>
                      <label className="block">
                        <span className={labelCls}>副标题</span>
                        <input
                          value={profile[block.key]?.subtitle || ''}
                          onChange={(e) => patchEntryFieldBlock(activeEntry, block.key, 'subtitle', e.target.value)}
                          className={inputCls}
                        />
                      </label>
                      <label className="block md:col-span-2">
                        <span className={labelCls}>输入框占位提示</span>
                        <input
                          value={profile[block.key]?.placeholder || ''}
                          onChange={(e) => patchEntryFieldBlock(activeEntry, block.key, 'placeholder', e.target.value)}
                          className={inputCls}
                        />
                      </label>
                    </div>
                  </div>
                ))}
                {FIELD_BLOCKS.every((b) => !isFieldBlockVisible(activeEntry, b.key)) && (
                  <p className="text-sm text-navy-500 py-4 text-center">请在上方勾选需要文案的输入区块</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {subTab === 'themes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(form.themes || []).map((item, idx) => (
            <div
              key={item.key}
              className={`glass-card rounded-2xl p-5 space-y-3 ${item.enabled === false ? 'opacity-50' : ''}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-2xl">{item.icon || '🎬'}</span>
                <label className="flex items-center gap-2 text-sm text-navy-200">
                  <input
                    type="checkbox"
                    checked={item.enabled !== false}
                    onChange={(e) => patchTheme(idx, 'enabled', e.target.checked)}
                  />
                  启用
                </label>
              </div>
              <div className="text-xs text-navy-500 font-mono">{item.key}</div>
              <label className="block">
                <span className={labelCls}>显示名称</span>
                <input
                  value={item.displayName || ''}
                  onChange={(e) => patchTheme(idx, 'displayName', e.target.value)}
                  className={inputCls}
                />
              </label>
              <div className="flex gap-2">
                <label className="block flex-1">
                  <span className={labelCls}>图标</span>
                  <input
                    value={item.icon || ''}
                    onChange={(e) => patchTheme(idx, 'icon', e.target.value)}
                    className={inputCls}
                  />
                </label>
                <label className="block">
                  <span className={labelCls}>色值</span>
                  <input
                    type="color"
                    value={item.color || '#667eea'}
                    onChange={(e) => patchTheme(idx, 'color', e.target.value)}
                    className="h-[42px] w-14 rounded-xl border border-navy-700/40 cursor-pointer"
                  />
                </label>
              </div>
            </div>
          ))}
        </div>
      )}

      {subTab === 'params' && (
        <div className="space-y-6">
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Gauge className="w-4 h-4 text-gold-400" /> 预算档位
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(form.budgetLevels || []).map((item, idx) => (
                <div key={item.key} className="p-4 rounded-xl bg-navy-900/40 border border-navy-700/40 space-y-2">
                  <div className="text-xs text-navy-500">{item.key}</div>
                  <input
                    value={item.name || ''}
                    placeholder="名称"
                    onChange={(e) => patchList('budgetLevels', idx, 'name', e.target.value)}
                    className={inputCls}
                  />
                  <textarea
                    rows={2}
                    value={item.description || ''}
                    placeholder="卡片说明（C 端选项下方）"
                    onChange={(e) => patchList('budgetLevels', idx, 'description', e.target.value)}
                    className={`${inputCls} resize-none text-xs`}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Compass className="w-4 h-4 text-gold-400" /> 目标平台
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {(form.platforms || []).map((item, idx) => (
                <div key={item.key} className="p-4 rounded-xl bg-navy-900/40 border border-navy-700/40 space-y-2">
                  <div className="text-xs text-navy-500">{item.key}</div>
                  <input
                    value={item.name || ''}
                    onChange={(e) => patchList('platforms', idx, 'name', e.target.value)}
                    className={inputCls}
                  />
                  <textarea
                    rows={2}
                    value={item.description || ''}
                    placeholder="平台特点说明"
                    onChange={(e) => patchList('platforms', idx, 'description', e.target.value)}
                    className={`${inputCls} resize-none text-xs`}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gold-400" /> 集数规则
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              {[
                ['min', '最小'],
                ['max', '最大'],
                ['step', '步进'],
                ['default', '默认'],
                ['durationMinutes', '每集分钟'],
              ].map(([field, label]) => (
                <label key={field} className="block">
                  <span className={labelCls}>{label}</span>
                  <input
                    type="number"
                    value={ep[field] ?? ''}
                    onChange={(e) => patchEpisode(field, e.target.value)}
                    className={inputCls}
                  />
                </label>
              ))}
            </div>
            <label className="block">
              <span className={labelCls}>快捷档位（逗号分隔，如 20, 40, 80, 100）</span>
              <input
                value={presetsText}
                onChange={(e) => patchEpisode('presetsText', e.target.value)}
                className={inputCls}
              />
            </label>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <LayoutList className="w-4 h-4 text-gold-400" /> 格式变体
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(form.formatVariants || []).map((item, idx) => (
                <div key={item.key} className="p-4 rounded-xl bg-navy-900/40 border border-navy-700/40 space-y-2">
                  <div className="text-xs text-navy-500">格式 {item.key}</div>
                  <input
                    value={item.name || ''}
                    onChange={(e) => patchList('formatVariants', idx, 'name', e.target.value)}
                    className={inputCls}
                  />
                  <textarea
                    rows={2}
                    value={item.description || ''}
                    placeholder="格式说明"
                    onChange={(e) => patchList('formatVariants', idx, 'description', e.target.value)}
                    className={`${inputCls} resize-none text-xs`}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {subTab === 'copy' && (
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <p className="text-sm text-navy-400 mb-2">修改 C 端各区块的标题与副标题（与具体入口无关的通用文案）</p>
          {Object.entries(form.sections || {}).map(([key, block]) => (
            <div key={key} className="p-4 rounded-xl bg-navy-900/30 border border-navy-700/40">
              <div className="text-sm text-gold-400/80 mb-3">{SECTION_TITLE_LABELS[key] || key}</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="block">
                  <span className={labelCls}>标题</span>
                  <input
                    value={block?.title || ''}
                    onChange={(e) => patchSection(key, 'title', e.target.value)}
                    className={inputCls}
                  />
                </label>
                <label className="block">
                  <span className={labelCls}>副标题</span>
                  <input
                    value={block?.subtitle || ''}
                    onChange={(e) => patchSection(key, 'subtitle', e.target.value)}
                    className={inputCls}
                  />
                </label>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="fixed bottom-0 left-0 right-0 md:left-64 z-30 px-6 py-4 bg-navy-950/90 border-t border-navy-800/60 backdrop-blur-md flex items-center justify-between gap-4">
        <p className="text-sm text-navy-400 hidden sm:block">
          配置包 {skillVersion || '—'} · 保存后 C 端刷新创作页生效
        </p>
        <button
          type="button"
          disabled={saving}
          onClick={save}
          className="ml-auto px-8 py-3 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold flex items-center gap-2 disabled:opacity-60 shadow-lg shadow-gold-500/20"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '保存并同步到 C 端'}
        </button>
      </div>
    </div>
  )
}

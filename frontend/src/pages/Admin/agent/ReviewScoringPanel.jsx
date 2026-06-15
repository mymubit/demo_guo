import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { Save } from 'lucide-react'
import { admin } from '@/services/api'

export default function ReviewScoringPanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [presets, setPresets] = useState([])
  const [presetId, setPresetId] = useState('standard')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [form, setForm] = useState({
    pass_threshold: 70,
    weights: { format: 20, rhythm: 40, content: 20, production: 20 },
    grade_thresholds: { S: 90, A: 80, B: 70, C: 60, D: 0 },
  })

  const weightLabels = { format: '格式', rhythm: '节奏', content: '内容', production: '制作' }

  function applyPreset(preset, { markCustom = false } = {}) {
    if (!preset) return
    setPresetId(markCustom ? 'custom' : preset.id)
    setForm({
      pass_threshold: preset.pass_threshold,
      weights: { ...preset.weights },
      grade_thresholds: { ...preset.grade_thresholds },
    })
  }

  async function load() {
    setLoading(true)
    try {
      const data = await admin.getReviewScoringConfig()
      if (data) {
        const list = Array.isArray(data.presets) ? data.presets : []
        setPresets(list)
        setPresetId(data.preset_id || 'standard')
        setShowAdvanced(data.preset_id === 'custom')
        setForm({
          pass_threshold: data.pass_threshold ?? 70,
          weights: {
            format: 20,
            rhythm: 40,
            content: 20,
            production: 20,
            ...(data.weights || {}),
          },
          grade_thresholds: {
            S: 90,
            A: 80,
            B: 70,
            C: 60,
            D: 0,
            ...(data.grade_thresholds || {}),
          },
        })
      }
    } catch (err) {
      onMessage(err.message || '加载失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function save(nextPresetId = presetId) {
    setSaving(true)
    try {
      await admin.saveReviewScoringConfig({
        preset_id: nextPresetId,
        pass_threshold: form.pass_threshold,
        weights: form.weights,
        grade_thresholds: form.grade_thresholds,
      })
      onMessage('审查策略已保存，ReviewAgent 与 C 端质检同步生效')
      await load()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  function handleSelectPreset(preset) {
    applyPreset(preset)
    setShowAdvanced(false)
  }

  function handleApplyAndSave(preset) {
    applyPreset(preset)
    setShowAdvanced(false)
    save(preset.id)
  }

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center text-navy-400">加载中…</div>
    )
  }

  const activePreset = presets.find((item) => item.id === presetId)

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5 max-w-3xl">
      <div className="glass-card rounded-2xl p-5 border border-blue-500/15 bg-blue-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          ReviewAgent（步骤 6）负责全剧质检与放行判定；ScoreAgent（步骤 7）负责深度评分与等级。此处配置审查策略与通过线，保存后影响新产生的质检结果。
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-white mb-3">审查策略</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {presets.map((preset) => {
            const active = presetId === preset.id
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`text-left rounded-2xl p-4 border transition-all ${
                  active
                    ? 'border-gold-400/50 bg-gold-400/10 ring-1 ring-gold-400/30'
                    : 'border-navy-700/40 bg-navy-900/30 hover:border-navy-600/60'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className={`font-semibold ${active ? 'text-gold-300' : 'text-white'}`}>
                    {preset.label}
                  </span>
                  <span className="text-xs text-navy-400 shrink-0">通过 ≥{preset.pass_threshold}</span>
                </div>
                <p className="text-xs text-navy-400 leading-relaxed mb-3">{preset.description}</p>
                <div className="flex flex-wrap gap-1.5 text-[11px] text-navy-500">
                  {Object.entries(preset.weights || {}).map(([key, val]) => (
                    <span key={key} className="px-2 py-0.5 rounded bg-navy-800/60">
                      {weightLabels[key] || key} {val}%
                    </span>
                  ))}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-white font-medium">
              当前：{activePreset?.label || (presetId === 'custom' ? '自定义' : '—')}
            </div>
            <div className="text-sm text-navy-400 mt-1">
              通过线 {form.pass_threshold} 分 · 节奏 {form.weights.rhythm}% · S 级 ≥
              {form.grade_thresholds.S} 分
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={saving || presetId === 'standard'}
              onClick={() => {
                const standard = presets.find((item) => item.id === 'standard')
                if (standard) handleApplyAndSave(standard)
              }}
              className="px-4 py-2 rounded-xl text-sm text-navy-200 border border-navy-600/40 hover:bg-navy-800/50 disabled:opacity-50"
            >
              恢复默认
            </button>
            <button
              type="button"
              disabled={saving || presetId === 'custom'}
              onClick={() => save(presetId)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? '保存中…' : '保存并生效'}
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="text-sm text-gold-400 hover:text-gold-300"
        >
          {showAdvanced ? '收起高级参数' : '展开高级参数（自定义权重与等级线）'}
        </button>

        {showAdvanced && (
          <div className="space-y-4 pt-2 border-t border-navy-700/40">
            <label className="block text-sm text-navy-300">
              通过分数线
              <input
                type="number"
                min={0}
                max={100}
                className="mt-1 w-full max-w-xs rounded-xl bg-navy-900 border border-navy-700 px-4 py-2 text-white"
                value={form.pass_threshold}
                onChange={(e) => {
                  setPresetId('custom')
                  setForm((f) => ({ ...f, pass_threshold: Number(e.target.value) }))
                }}
              />
            </label>
            <div>
              <div className="text-sm text-navy-300 mb-2">维度权重（%）</div>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(weightLabels).map(([key, label]) => (
                  <label key={key} className="block text-xs text-navy-400">
                    {label}
                    <input
                      type="number"
                      min={0}
                      max={100}
                      className="mt-1 w-full rounded-xl bg-navy-900 border border-navy-700 px-3 py-2 text-white"
                      value={form.weights[key] ?? 0}
                      onChange={(e) => {
                        setPresetId('custom')
                        setForm((f) => ({
                          ...f,
                          weights: { ...f.weights, [key]: Number(e.target.value) },
                        }))
                      }}
                    />
                  </label>
                ))}
              </div>
            </div>
            <div>
              <div className="text-sm text-navy-300 mb-2">等级阈值</div>
              <div className="grid grid-cols-5 gap-2">
                {['S', 'A', 'B', 'C', 'D'].map((g) => (
                  <label key={g} className="block text-xs text-navy-400 text-center">
                    {g}
                    <input
                      type="number"
                      min={0}
                      max={100}
                      className="mt-1 w-full rounded-xl bg-navy-900 border border-navy-700 px-2 py-2 text-white text-center"
                      value={form.grade_thresholds[g] ?? 0}
                      onChange={(e) => {
                        setPresetId('custom')
                        setForm((f) => ({
                          ...f,
                          grade_thresholds: { ...f.grade_thresholds, [g]: Number(e.target.value) },
                        }))
                      }}
                    />
                  </label>
                ))}
              </div>
            </div>
            <button
              type="button"
              onClick={() => save('custom')}
              disabled={saving}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-navy-800 text-gold-300 border border-gold-500/30 text-sm disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              保存自定义参数
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

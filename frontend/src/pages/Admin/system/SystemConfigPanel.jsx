import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { Save } from 'lucide-react'
import { admin } from '@/services/api'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'

function skillConfigLabel(config) {
  const desc = (config.description || '').trim()
  if (desc) {
    const head = desc.split('（')[0].split('(')[0].trim()
    if (head && head.length <= 32) return head
  }
  return config.key
}

export default function SystemConfigPanel({ onMessage }) {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingKey, setEditingKey] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [savingKey, setSavingKey] = useState(null)

  useEffect(() => {
    admin
      .getSkillConfigs()
      .then((data) => setConfigs(Array.isArray(data) ? data : []))
      .catch((err) => onMessage(err.message || '加载系统配置失败', 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function startEdit(config) {
    setEditingKey(config.key)
    setEditValue(String(config.value))
  }

  async function saveEdit(config) {
    if (savingKey) return
    setSavingKey(config.key)
    try {
      await admin.updateSkillConfig(config.key, editValue)
      setConfigs((prev) =>
        prev.map((c) => (c.key === config.key ? { ...c, value: editValue } : c))
      )
      setEditingKey(null)
      onMessage(`已更新：${skillConfigLabel(config)}`)
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSavingKey(null)
    }
  }

  function cancelEdit() {
    if (selectedConfig) {
      setEditValue(String(selectedConfig.value))
    } else {
      setEditingKey(null)
      setEditValue('')
    }
  }

  const filteredConfigs = configs.filter((c) => !String(c.key || '').startsWith('llm.'))
  const [selectedKey, setSelectedKey] = useAdminSelection(filteredConfigs, (config) => config.key)
  const selectedConfig = filteredConfigs.find((config) => config.key === selectedKey)

  useEffect(() => {
    if (selectedConfig) {
      setEditingKey(selectedConfig.key)
      setEditValue(String(selectedConfig.value))
    }
  }, [selectedConfig?.key])

  if (loading) {
    return <div className="text-center py-16 text-navy-400">加载系统配置…</div>
  }

  if (!filteredConfigs.length) {
    return (
      <div className="glass-card rounded-2xl py-16 text-center text-navy-400">
        暂无系统配置，请联系管理员初始化数据
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className="glass-card rounded-2xl p-5 border border-blue-500/15 bg-blue-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          引擎内部开关与默认值。列表用中文说明，括号内为程序标识；大模型相关请用「模型中心」与「Agent 中心」。
        </p>
      </div>
      <AdminMasterDetail
        listTitle="参数列表"
        items={filteredConfigs}
        selectedId={selectedKey}
        onSelect={setSelectedKey}
        getId={(config) => config.key}
        sidebarWidthClass="lg:grid-cols-[280px_minmax(0,1fr)]"
        renderListItem={(config, { active, onSelect }) => (
          <AdminMasterDetailListButton
            key={config.key}
            active={active}
            onClick={onSelect}
            title={skillConfigLabel(config)}
            subtitle={config.key}
          />
        )}
        renderDetail={(config) => (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-white">{skillConfigLabel(config)}</h3>
              <code className="text-xs text-navy-500 font-mono">{config.key}</code>
              <p className="text-sm text-navy-300 mt-2">{config.description || '—'}</p>
            </div>
            <div>
              <div className="text-xs text-navy-500 mb-2">当前值</div>
              {config.type === 'select' ? (
                <select
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full max-w-md px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm"
                >
                  {config.options.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              ) : config.type === 'boolean' ? (
                <select
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full max-w-md px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm"
                >
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              ) : (
                <input
                  type={config.type === 'number' ? 'number' : 'text'}
                  value={editValue}
                  min={config.min}
                  max={config.max}
                  step={config.step}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full max-w-md px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm font-mono"
                />
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => saveEdit(config)}
                disabled={savingKey === config.key}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-60"
              >
                <Save className="w-4 h-4" />
                {savingKey === config.key ? '保存中…' : '保存'}
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="px-4 py-2.5 rounded-xl bg-navy-800/60 text-navy-200 text-sm"
              >
                重置
              </button>
            </div>
          </div>
        )}
      />
    </motion.div>
  )
}

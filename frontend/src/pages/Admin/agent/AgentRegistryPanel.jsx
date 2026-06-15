import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw, Save, Upload } from 'lucide-react'
import { admin } from '@/services/api'

const inputCls =
  'w-full px-3 py-2 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:border-gold-500/50 outline-none'
const labelCls = 'text-xs text-navy-400 mb-1 block'

function csvToList(text) {
  return String(text || '')
    .split(/[,，\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

function listToCsv(list) {
  return (list || []).join(', ')
}

function cloneRegistry(registry) {
  return JSON.parse(JSON.stringify(registry || {}))
}

const SUB_SKILL_TYPES = ['rule', 'cli', 'retrieval', 'llm', 'llm+rule', 'retrieval+rule', 'trace']

function emptySubSkill() {
  return { id: '', type: 'rule', description: '' }
}

function Tier1SectionPicker({ catalog = [], selected = [], onChange }) {
  const selectedSet = new Set(selected || [])
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {catalog.map((section) => {
          const key = section.key || section
          const label = section.label || key
          const active = selectedSet.has(key)
          return (
            <button
              key={key}
              type="button"
              title={key}
              onClick={() => {
                const next = active
                  ? selected.filter((item) => item !== key)
                  : [...selected, key]
                onChange(next)
              }}
              className={`px-2 py-1 rounded-lg text-[11px] border transition-colors ${
                active
                  ? 'bg-gold-400/15 text-gold-300 border-gold-400/40'
                  : 'bg-navy-900/50 text-navy-400 border-navy-700/40 hover:border-navy-600'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>
      {!catalog.length ? (
        <p className="text-xs text-navy-500">暂无 Tier1 目录，请检查 skill rule renderers。</p>
      ) : null}
      <label className="block">
        <span className={labelCls}>手动编辑（逗号分隔）</span>
        <input
          value={listToCsv(selected)}
          onChange={(e) => onChange(csvToList(e.target.value))}
          className={`${inputCls} font-mono text-xs`}
        />
      </label>
    </div>
  )
}

function SubSkillEditor({ skills = [], onChange }) {
  function patchSkill(index, field, value) {
    const next = skills.map((item, idx) => (idx === index ? { ...item, [field]: value } : item))
    onChange(next)
  }

  function removeSkill(index) {
    onChange(skills.filter((_, idx) => idx !== index))
  }

  function addSkill() {
    onChange([...(skills || []), emptySubSkill()])
  }

  function moveSkill(index, delta) {
    const target = index + delta
    if (target < 0 || target >= skills.length) return
    const next = [...skills]
    ;[next[index], next[target]] = [next[target], next[index]]
    onChange(next)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-navy-400">子技能 ({skills.length})</span>
        <button
          type="button"
          onClick={addSkill}
          className="text-xs text-gold-400 hover:text-gold-300"
        >
          + 添加子技能
        </button>
      </div>
      {skills.map((skill, index) => (
        <div
          key={`${skill.id || 'skill'}-${index}`}
          className="p-3 rounded-xl border border-navy-700/40 bg-navy-950/40 space-y-2"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] text-navy-500 font-mono">#{index + 1}</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={index === 0}
                onClick={() => moveSkill(index, -1)}
                className="text-[10px] text-navy-400 hover:text-navy-200 disabled:opacity-30"
              >
                上移
              </button>
              <button
                type="button"
                disabled={index >= skills.length - 1}
                onClick={() => moveSkill(index, 1)}
                className="text-[10px] text-navy-400 hover:text-navy-200 disabled:opacity-30"
              >
                下移
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <label className="block">
              <span className={labelCls}>id</span>
              <input
                value={skill.id || ''}
                onChange={(e) => patchSkill(index, 'id', e.target.value)}
                className={`${inputCls} font-mono text-xs`}
              />
            </label>
            <label className="block">
              <span className={labelCls}>type</span>
              <select
                value={skill.type || 'rule'}
                onChange={(e) => patchSkill(index, 'type', e.target.value)}
                className={`${inputCls} text-xs`}
              >
                {SUB_SKILL_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block">
            <span className={labelCls}>description</span>
            <input
              value={skill.description || ''}
              onChange={(e) => patchSkill(index, 'description', e.target.value)}
              className={`${inputCls} text-xs`}
            />
          </label>
          {['cli', 'llm', 'llm+rule', 'retrieval+rule'].includes(skill.type) ? (
            <label className="block">
              <span className={labelCls}>cli（CLI 子技能）</span>
              <input
                value={skill.cli || ''}
                onChange={(e) => patchSkill(index, 'cli', e.target.value)}
                className={`${inputCls} font-mono text-xs`}
                placeholder="sub-brief"
              />
            </label>
          ) : null}
          {String(skill.type || '').includes('llm') ? (
            <label className="block">
              <span className={labelCls}>handbook</span>
              <input
                value={skill.handbook || ''}
                onChange={(e) => patchSkill(index, 'handbook', e.target.value)}
                className={`${inputCls} font-mono text-xs`}
                placeholder="nodes/node-2-structure.md"
              />
            </label>
          ) : null}
          {String(skill.type || '').includes('retrieval') ? (
            <label className="block">
              <span className={labelCls}>references（逗号分隔）</span>
              <input
                value={listToCsv(skill.references)}
                onChange={(e) => patchSkill(index, 'references', csvToList(e.target.value))}
                className={`${inputCls} font-mono text-xs`}
              />
            </label>
          ) : null}
          <button
            type="button"
            onClick={() => removeSkill(index)}
            className="text-xs text-red-400/80 hover:text-red-300"
          >
            移除
          </button>
        </div>
      ))}
    </div>
  )
}

export default function AgentRegistryPanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [migrating, setMigrating] = useState(false)
  const [expandedAgentId, setExpandedAgentId] = useState(null)
  const [expandedSection, setExpandedSection] = useState('skill')
  const [tier1Catalog, setTier1Catalog] = useState([])
  const [tier1Presets, setTier1Presets] = useState({})
  const [meta, setMeta] = useState({})
  const [registry, setRegistry] = useState({})
  const [jsonText, setJsonText] = useState('')

  async function load() {
    setLoading(true)
    try {
      const data = await admin.getAgentRegistryConfig()
      const reg = data?.registry || {}
      setMeta({
        source: data?.source,
        config_id: data?.config_id,
        updated_at: data?.updated_at,
        file_version: data?.file_version,
        file_path: data?.file_path,
      })
      setRegistry(reg)
      setJsonText(JSON.stringify(reg, null, 2))
      setTier1Catalog(Array.isArray(data?.tier1SectionCatalog) ? data.tier1SectionCatalog : [])
      setTier1Presets(data?.defaultTier1SectionsByAgent || {})
    } catch (err) {
      onMessage(err.message || '加载技能注册表失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const agents = registry?.agents || []
  const registryMeta = registry?._meta || {}

  const workspaceModules = registryMeta.workspace_modules || []
  const postScriptIndex = registryMeta.post_script_pipeline_index || []

  function patchMeta(field, value) {
    setRegistry((prev) => ({
      ...prev,
      _meta: { ...(prev._meta || {}), [field]: value },
    }))
  }

  function patchAgentPrompt(agentId, field, value) {
    setRegistry((prev) => ({
      ...prev,
      agents: (prev.agents || []).map((a) => {
        if (a.id !== agentId) return a
        const prompt = { ...(a.prompt || {}), [field]: value }
        return { ...a, prompt }
      }),
    }))
  }

  function patchAgent(agentId, field, value) {
    setRegistry((prev) => ({
      ...prev,
      agents: (prev.agents || []).map((a) =>
        a.id === agentId ? { ...a, [field]: value } : a
      ),
    }))
  }

  function patchAgentSubSkills(agentId, subSkills) {
    patchAgent(agentId, 'sub_skills', subSkills)
  }

  function patchModule(listKey, index, field, value) {
    setRegistry((prev) => {
      const nextMeta = { ...(prev._meta || {}) }
      const list = [...(nextMeta[listKey] || [])]
      list[index] = { ...list[index], [field]: value }
      nextMeta[listKey] = list
      return { ...prev, _meta: nextMeta }
    })
  }

  async function persistRegistry(body) {
    const data = await admin.saveAgentRegistryConfig({ registry: body })
    setRegistry(data?.registry || body)
    setJsonText(JSON.stringify(data?.registry || body, null, 2))
    setMeta((prev) => ({
      ...prev,
      source: data?.source || 'db',
      updated_at: data?.updated_at,
    }))
    onMessage('技能注册表已保存，运行时立即生效')
  }

  async function save() {
    setSaving(true)
    try {
      await persistRegistry(cloneRegistry(registry))
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function saveFromJson() {
    let body
    try {
      body = JSON.parse(jsonText)
    } catch {
      onMessage('JSON 格式无效，请检查后再保存', 'error')
      return
    }
    if (!body || typeof body !== 'object') {
      onMessage('registry 必须是 JSON 对象', 'error')
      return
    }
    setSaving(true)
    try {
      await persistRegistry(body)
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function migrateSkillConfig() {
    setMigrating(true)
    try {
      const data = await admin.migrateAgentSkillConfig()
      setRegistry(data?.registry || registry)
      setJsonText(JSON.stringify(data?.registry || registry, null, 2))
      onMessage(`已迁移 ${data?.migrated_count ?? 0} 个技能配置`)
    } catch (err) {
      onMessage(err.message || '迁移失败', 'error')
    } finally {
      setMigrating(false)
    }
  }

  async function importFromFile() {
    setImporting(true)
    try {
      const data = await admin.importAgentRegistryFromFile({ overwrite: true })
      setRegistry(data?.registry || {})
      setJsonText(JSON.stringify(data?.registry || {}, null, 2))
      setMeta((prev) => ({
        ...prev,
        source: data?.source || 'db',
        updated_at: data?.updated_at,
      }))
      onMessage('已从磁盘 registry.json 导入')
    } catch (err) {
      onMessage(err.message || '导入失败', 'error')
    } finally {
      setImporting(false)
    }
  }

  if (loading) {
    return <div className="text-center py-16 text-navy-400">加载技能注册表…</div>
  }

  return (
    <>
      <div className="space-y-5 pb-8">
      <div className="glass-card rounded-2xl p-5 border border-purple-500/20 bg-purple-500/5">
        <h2 className="text-lg font-bold text-white mb-1">Agent 注册表（高级）</h2>
        <p className="text-sm text-navy-300 leading-relaxed">
          日常主链步骤、Prompt、Tier1、模型请优先在
          <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
            主链工作室
          </Link>
          维护。此页用于批量 Agent 定义、后处理元数据与全量 JSON。
        </p>
        <div className="flex flex-wrap gap-3 mt-3 text-xs text-navy-400">
          <span>
            来源：<strong className="text-gold-300">{meta.source || '—'}</strong>
          </span>
          <span>版本：{registryMeta.version || meta.file_version || '—'}</span>
          {meta.updated_at ? <span>更新：{meta.updated_at}</span> : null}
        </div>
      </div>

      <div className="space-y-5">
          <section className="glass-card rounded-2xl p-5 space-y-4">
            <h3 className="text-white font-semibold">编排元数据 (_meta)</h3>
            <p className="text-xs text-navy-500">
              后处理链也可在
              <Link to="/admin/main-chain" className="text-gold-400 hover:underline mx-1">
                主链工作室
              </Link>
              编辑。
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="block md:col-span-2">
                <span className={labelCls}>后处理链 post_script_chain（逗号分隔 agent id）</span>
                <input
                  value={listToCsv(registryMeta.post_script_chain)}
                  onChange={(e) => patchMeta('post_script_chain', csvToList(e.target.value))}
                  className={inputCls}
                  placeholder="review, polish, review, score"
                />
                <p className="text-[11px] text-navy-500 mt-1">
                  可重复同一 agent（如 polish 前后各 review 一次）；顺序即执行顺序。
                </p>
              </label>
              <label className="block md:col-span-2">
                <span className={labelCls}>剧本完成后追加 Agent（post_script_append_agents）</span>
                <input
                  value={listToCsv(registryMeta.post_script_append_agents)}
                  onChange={(e) => patchMeta('post_script_append_agents', csvToList(e.target.value))}
                  className={inputCls}
                  placeholder="marketing"
                />
              </label>
              <label className="block">
                <span className={labelCls}>Polish 最大轮次</span>
                <input
                  type="number"
                  min="0"
                  value={registryMeta.polish_max_rounds ?? 2}
                  onChange={(e) => patchMeta('polish_max_rounds', Number(e.target.value) || 0)}
                  className={inputCls}
                />
              </label>
            </div>

            <div>
              <h4 className="text-sm text-gold-400/90 mb-2">工作台映射 workspace_modules</h4>
              <div className="space-y-2">
                {workspaceModules.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2">
                    <input
                      type="number"
                      value={item.index ?? ''}
                      onChange={(e) => patchModule('workspace_modules', idx, 'index', Number(e.target.value))}
                      className={inputCls}
                      placeholder="index"
                    />
                    <input
                      value={item.agent_id || ''}
                      onChange={(e) => patchModule('workspace_modules', idx, 'agent_id', e.target.value)}
                      className={inputCls}
                      placeholder="agent_id"
                    />
                    <input
                      value={item.label || ''}
                      onChange={(e) => patchModule('workspace_modules', idx, 'label', e.target.value)}
                      className={inputCls}
                      placeholder="label"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm text-gold-400/90 mb-2">后处理步骤映射 post_script_pipeline_index</h4>
              <div className="space-y-2">
                {postScriptIndex.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-2 gap-2 max-w-md">
                    <input
                      type="number"
                      value={item.index ?? ''}
                      onChange={(e) =>
                        patchModule('post_script_pipeline_index', idx, 'index', Number(e.target.value))
                      }
                      className={inputCls}
                    />
                    <input
                      value={item.agent_id || ''}
                      onChange={(e) =>
                        patchModule('post_script_pipeline_index', idx, 'agent_id', e.target.value)
                      }
                      className={inputCls}
                    />
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="glass-card rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-3">技能列表 ({agents.length})</h3>
            <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="p-4 rounded-xl border border-navy-700/40 bg-navy-900/30 space-y-2"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-white font-medium">{agent.name_zh || agent.name || agent.id}</span>
                    <code className="text-[10px] text-navy-500">{agent.id}</code>
                    {agent.workspace_index ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-navy-800 text-navy-300">
                        步骤 {agent.workspace_index}
                      </span>
                    ) : null}
                  </div>
                  <label className="block">
                    <span className={labelCls}>runner 路径</span>
                    <input
                      value={agent.runner || agent.runner_path || ''}
                      onChange={(e) => patchAgent(agent.id, 'runner', e.target.value)}
                      className={`${inputCls} font-mono text-xs`}
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      if (expandedAgentId === agent.id) {
                        setExpandedAgentId(null)
                        return
                      }
                      setExpandedAgentId(agent.id)
                      setExpandedSection('skill')
                    }}
                    className="text-xs text-gold-400 hover:text-gold-300"
                  >
                    {expandedAgentId === agent.id ? '收起技能配置' : '编辑 Tier1 / Prompt / 子技能'}
                  </button>
                  {expandedAgentId === agent.id ? (
                    <div className="space-y-3 pt-2 border-t border-navy-700/40">
                      <div className="flex flex-wrap gap-2">
                        {['skill', 'sub_skills'].map((section) => (
                          <button
                            key={section}
                            type="button"
                            onClick={() => setExpandedSection(section)}
                            className={`px-2 py-1 rounded-lg text-xs border ${
                              expandedSection === section
                                ? 'bg-purple-500/15 text-purple-200 border-purple-400/30'
                                : 'bg-navy-900/40 text-navy-400 border-navy-700/40'
                            }`}
                          >
                            {section === 'skill' ? 'Tier1 / Prompt' : '子技能'}
                          </button>
                        ))}
                      </div>
                      {expandedSection === 'skill' ? (
                        <>
                          <label className="block">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <span className={labelCls}>Tier1 注入分区</span>
                              {Array.isArray(tier1Presets[agent.id]) && tier1Presets[agent.id].length ? (
                                <button
                                  type="button"
                                  onClick={() =>
                                    patchAgent(agent.id, 'tier1_sections', [...tier1Presets[agent.id]])
                                  }
                                  className="text-[11px] text-gold-400 hover:text-gold-300"
                                >
                                  应用推荐预设 ({tier1Presets[agent.id].length})
                                </button>
                              ) : null}
                            </div>
                            <Tier1SectionPicker
                              catalog={tier1Catalog}
                              selected={agent.tier1_sections || []}
                              onChange={(sections) => patchAgent(agent.id, 'tier1_sections', sections)}
                            />
                          </label>
                          <label className="block">
                            <span className={labelCls}>System Prompt</span>
                            <textarea
                              rows={4}
                              value={agent.prompt?.system || ''}
                              onChange={(e) => patchAgentPrompt(agent.id, 'system', e.target.value)}
                              className={`${inputCls} font-mono text-xs resize-y`}
                            />
                          </label>
                          <label className="block">
                            <span className={labelCls}>User 模板（{'{upstream_json}'}）</span>
                            <textarea
                              rows={3}
                              value={agent.prompt?.userTemplate || agent.prompt?.user_prompt_tpl || ''}
                              onChange={(e) => patchAgentPrompt(agent.id, 'userTemplate', e.target.value)}
                              className={`${inputCls} font-mono text-xs resize-y`}
                            />
                          </label>
                          <label className="block">
                            <span className={labelCls}>附加约束</span>
                            <textarea
                              rows={2}
                              value={agent.prompt?.constraints || ''}
                              onChange={(e) => patchAgentPrompt(agent.id, 'constraints', e.target.value)}
                              className={`${inputCls} text-xs resize-y`}
                            />
                          </label>
                        </>
                      ) : (
                        <SubSkillEditor
                          skills={agent.sub_skills || []}
                          onChange={(skills) => patchAgentSubSkills(agent.id, skills)}
                        />
                      )}
                    </div>
                  ) : null}
                  <p className="text-xs text-navy-500">
                    outputs: {(agent.outputs || []).join(', ') || '—'} · tier1:{' '}
                    {(agent.tier1_sections || []).length} · sub_skills: {(agent.sub_skills || []).length}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <details className="glass-card rounded-2xl border border-navy-700/40 overflow-hidden group">
          <summary className="cursor-pointer list-none px-5 py-4 text-sm text-navy-400 select-none flex items-center justify-between">
            <span>开发者 · JSON 全量编辑</span>
            <span className="text-[10px] text-navy-600 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-5 pb-5 space-y-3 border-t border-navy-800/60 pt-4">
            <p className="text-xs text-navy-500 leading-relaxed">
              直接编辑完整 registry.json 结构。保存前请确认 JSON 合法；日常配置建议使用上方结构化表单或主链工作室。
            </p>
            <textarea
              rows={20}
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              className="w-full font-mono text-xs px-4 py-3 rounded-2xl bg-navy-950 border border-navy-700/40 text-navy-100"
              spellCheck={false}
            />
            <div className="flex justify-end">
              <button
                type="button"
                disabled={saving}
                onClick={saveFromJson}
                className="px-4 py-2 rounded-xl bg-navy-800/70 text-gold-300 text-sm border border-gold-500/25 disabled:opacity-50"
              >
                从 JSON 保存
              </button>
            </div>
          </div>
        </details>
      </div>

      <div className="fixed bottom-0 left-0 right-0 md:left-64 z-30 px-6 py-4 bg-navy-950/90 border-t border-navy-800/60 backdrop-blur-md flex items-center justify-end gap-3">
        <button
          type="button"
          disabled={migrating}
          onClick={migrateSkillConfig}
          className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-100 text-sm disabled:opacity-60"
        >
          {migrating ? '迁移中…' : '迁移流水线遗留配置'}
        </button>
        <button
          type="button"
          disabled={importing}
          onClick={importFromFile}
          className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-100 text-sm flex items-center gap-2 disabled:opacity-60"
        >
          <Upload className="w-4 h-4" />
          {importing ? '导入中…' : '从磁盘导入'}
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={load}
          className="px-4 py-2.5 rounded-xl bg-navy-800/70 text-navy-100 text-sm flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={save}
          className="px-8 py-3 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold flex items-center gap-2 disabled:opacity-60"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中…' : '保存并生效'}
        </button>
      </div>
    </>
  )
}

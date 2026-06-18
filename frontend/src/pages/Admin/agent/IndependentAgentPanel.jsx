import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Plus, RefreshCw, Save, Trash2 } from 'lucide-react'
import { admin } from '@/services/api'
import { AdminEmpty, AdminLoading, AdminTabBar } from '@/components/admin/AdminUI'
import {
  AdminHealthBadges,
  AdminPenetrationLink,
  adminBtnPrimary,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'
import { cn } from '@/utils/cn'

const inputCls = 'sf-control text-sm w-full'
const labelCls = 'sf-label text-xs'

const AGENT_DETAIL_TABS = [
  { key: 'overview', label: '概览' },
  { key: 'prompt', label: 'Prompt' },
  { key: 'knowledge', label: 'Knowledge' },
  { key: 'contracts', label: '契约' },
  { key: 'runs', label: '最近运行' },
]

const emptyPromptForm = () => ({
  version: '',
  system_prompt: '',
  user_prompt_template: '',
  output_format_prompt: '',
  constraints_prompt: '',
  change_notes: '',
})

const emptyKnowledgeForm = () => ({
  knowledge_id: '',
  title: '',
  category: 'knowledge',
  content_text: '',
  priority: 100,
  is_enabled: true,
})

const emptyBindingForm = () => ({
  knowledge_id: '',
  binding_type: 'optional',
  inject_position: 'context',
  order_index: 0,
})

function lineDiff(leftText = '', rightText = '') {
  const leftLines = String(leftText || '').split('\n')
  const rightLines = String(rightText || '').split('\n')
  const max = Math.max(leftLines.length, rightLines.length)
  const rows = []
  for (let i = 0; i < max; i += 1) {
    const l = leftLines[i] ?? ''
    const r = rightLines[i] ?? ''
    if (l === r) {
      rows.push({ type: 'same', left: l, right: r })
    } else {
      rows.push({ type: 'diff', left: l, right: r })
    }
  }
  return rows
}

function PromptVersionDiff({ prompts = [] }) {
  const [leftVersion, setLeftVersion] = useState('')
  const [rightVersion, setRightVersion] = useState('')

  useEffect(() => {
    if (prompts.length >= 2 && !leftVersion && !rightVersion) {
      setLeftVersion(prompts[1]?.version || '')
      setRightVersion(prompts[0]?.version || '')
    }
  }, [prompts, leftVersion, rightVersion])

  const left = prompts.find((p) => p.version === leftVersion)
  const right = prompts.find((p) => p.version === rightVersion)
  const fields = ['system_prompt', 'user_prompt_template', 'output_format_prompt', 'constraints_prompt']

  if (prompts.length < 2) {
    return <p className="text-xs text-navy-400">至少两个 Prompt 版本才可对比</p>
  }

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/20 p-4">
      <h4 className="text-sm font-medium text-white">Prompt 版本对比</h4>
      <div className="grid grid-cols-2 gap-2">
        <select className={inputCls} value={leftVersion} onChange={(e) => setLeftVersion(e.target.value)}>
          {prompts.map((p) => (
            <option key={p.id} value={p.version}>{p.version}</option>
          ))}
        </select>
        <select className={inputCls} value={rightVersion} onChange={(e) => setRightVersion(e.target.value)}>
          {prompts.map((p) => (
            <option key={p.id} value={p.version}>{p.version}</option>
          ))}
        </select>
      </div>
      {fields.map((field) => {
        const rows = lineDiff(left?.[field], right?.[field])
        const hasDiff = rows.some((row) => row.type === 'diff')
        if (!hasDiff && !left?.[field] && !right?.[field]) return null
        return (
          <details key={field} open={hasDiff} className="rounded-lg border border-white/5">
            <summary className="cursor-pointer px-3 py-2 text-xs text-gold-300">{field}{hasDiff ? ' · 有差异' : ''}</summary>
            <div className="grid grid-cols-2 gap-2 px-3 pb-3 text-[11px] font-mono">
              <pre className="whitespace-pre-wrap text-navy-300 max-h-48 overflow-y-auto">{left?.[field] || '—'}</pre>
              <pre className="whitespace-pre-wrap text-navy-200 max-h-48 overflow-y-auto">{right?.[field] || '—'}</pre>
            </div>
          </details>
        )
      })}
    </div>
  )
}

export default function IndependentAgentPanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [agents, setAgents] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState(null)
  const [prompts, setPrompts] = useState([])
  const [bindings, setBindings] = useState([])
  const [knowledgeRows, setKnowledgeRows] = useState([])
  const [recentRuns, setRecentRuns] = useState([])
  const [saving, setSaving] = useState(false)
  const [runtimePolicyText, setRuntimePolicyText] = useState('{}')
  const [inputContractText, setInputContractText] = useState('{}')
  const [outputContractText, setOutputContractText] = useState('{}')
  const [editingPromptVersion, setEditingPromptVersion] = useState('')
  const [promptForm, setPromptForm] = useState(emptyPromptForm())
  const [knowledgeQuery, setKnowledgeQuery] = useState('')
  const [editingKnowledgeId, setEditingKnowledgeId] = useState('')
  const [knowledgeForm, setKnowledgeForm] = useState(emptyKnowledgeForm())
  const [bindingForm, setBindingForm] = useState(emptyBindingForm())
  const [detailTab, setDetailTab] = useState('overview')

  const filteredKnowledge = useMemo(() => {
    const q = knowledgeQuery.trim().toLowerCase()
    if (!q) return knowledgeRows
    return knowledgeRows.filter(
      (row) =>
        (row.knowledge_id || '').toLowerCase().includes(q) ||
        (row.title || '').toLowerCase().includes(q) ||
        (row.category || '').toLowerCase().includes(q),
    )
  }, [knowledgeQuery, knowledgeRows])

  const loadAgents = useCallback(async () => {
    setLoading(true)
    try {
      const rows = await admin.listIndependentAgents()
      setAgents(rows)
      if (!selectedId && rows[0]) setSelectedId(rows[0].agent_id)
    } catch (err) {
      onMessage(err.message || '加载独立 Agent 失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [onMessage, selectedId])

  const loadKnowledge = useCallback(async () => {
    try {
      const rows = await admin.listIndependentKnowledge()
      setKnowledgeRows(rows)
    } catch (err) {
      onMessage(err.message || '加载 Knowledge 失败', 'error')
    }
  }, [onMessage])

  const loadDetail = useCallback(async (agentId) => {
    if (!agentId) return
    try {
      const [agent, promptRows, bindingRows, runs] = await Promise.all([
        admin.getIndependentAgent(agentId),
        admin.listIndependentAgentPrompts(agentId),
        admin.listIndependentAgentBindings(agentId),
        admin.listIndependentAgentRuns({ agentId, limit: 12 }),
      ])
      setDetail(agent)
      setPrompts(promptRows)
      setBindings(bindingRows)
      setRecentRuns(runs)
      setRuntimePolicyText(JSON.stringify(agent?.runtime_policy || {}, null, 2))
      setInputContractText(JSON.stringify(agent?.input_contract || {}, null, 2))
      setOutputContractText(JSON.stringify(agent?.output_contract || {}, null, 2))
      setEditingPromptVersion('')
      setPromptForm(emptyPromptForm())
      setBindingForm(emptyBindingForm())
    } catch (err) {
      onMessage(err.message || '加载 Agent 详情失败', 'error')
    }
  }, [onMessage])

  useEffect(() => {
    loadAgents()
    loadKnowledge()
  }, [loadAgents, loadKnowledge])

  useEffect(() => {
    if (selectedId) loadDetail(selectedId)
  }, [selectedId, loadDetail])

  async function handleSave() {
    if (!selectedId || !detail) return
    setSaving(true)
    try {
      const runtimePolicy = JSON.parse(runtimePolicyText)
      const inputContract = JSON.parse(inputContractText)
      const outputContract = JSON.parse(outputContractText)
      await admin.saveIndependentAgent(selectedId, {
        name: detail.name,
        name_zh: detail.name_zh,
        description: detail.description,
        is_enabled: detail.is_enabled,
        lifecycle_status: detail.lifecycle_status,
        workspace_order: detail.workspace_order,
        default_output_artifact_key: detail.default_output_artifact_key,
        runtime_policy: runtimePolicy,
        input_contract: inputContract,
        output_contract: outputContract,
      })
      onMessage('Agent 已保存', 'success')
      await loadDetail(selectedId)
      await loadAgents()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleActivatePrompt(version) {
    try {
      await admin.activateIndependentAgentPrompt(selectedId, version)
      onMessage(`Prompt ${version} 已激活`, 'success')
      await loadDetail(selectedId)
    } catch (err) {
      onMessage(err.message || '激活失败', 'error')
    }
  }

  function openPromptEditor(prompt) {
    setEditingPromptVersion(prompt?.version || '')
    setPromptForm(
      prompt
        ? {
            version: prompt.version,
            system_prompt: prompt.system_prompt || '',
            user_prompt_template: prompt.user_prompt_template || '',
            output_format_prompt: prompt.output_format_prompt || '',
            constraints_prompt: prompt.constraints_prompt || '',
            change_notes: prompt.change_notes || '',
          }
        : { ...emptyPromptForm(), version: `v${Date.now()}` },
    )
  }

  async function handleSavePrompt() {
    if (!selectedId || !promptForm.version.trim()) {
      onMessage('请填写 Prompt 版本号', 'error')
      return
    }
    try {
      await admin.saveIndependentAgentPrompt(selectedId, promptForm)
      onMessage('Prompt 已保存', 'success')
      await loadDetail(selectedId)
    } catch (err) {
      onMessage(err.message || '保存 Prompt 失败', 'error')
    }
  }

  async function openKnowledgeEditor(knowledgeId) {
    if (!knowledgeId) {
      setEditingKnowledgeId('__new__')
      setKnowledgeForm(emptyKnowledgeForm())
      return
    }
    try {
      const row = await admin.getIndependentKnowledge(knowledgeId)
      setEditingKnowledgeId(knowledgeId)
      setKnowledgeForm({
        knowledge_id: row.knowledge_id,
        title: row.title || '',
        category: row.category || 'knowledge',
        content_text: row.content_text || '',
        priority: row.priority ?? 100,
        is_enabled: row.is_enabled !== false,
      })
    } catch (err) {
      onMessage(err.message || '加载 Knowledge 失败', 'error')
    }
  }

  async function handleSaveKnowledge() {
    if (!knowledgeForm.knowledge_id.trim()) {
      onMessage('请填写 knowledge_id', 'error')
      return
    }
    try {
      await admin.saveIndependentKnowledge(knowledgeForm)
      onMessage('Knowledge 已保存', 'success')
      setEditingKnowledgeId('')
      await loadKnowledge()
    } catch (err) {
      onMessage(err.message || '保存 Knowledge 失败', 'error')
    }
  }

  async function handleDeleteKnowledge(knowledgeId) {
    if (!window.confirm(`确认停用 Knowledge「${knowledgeId}」？`)) return
    try {
      await admin.deleteIndependentKnowledge(knowledgeId)
      onMessage('Knowledge 已停用', 'success')
      if (editingKnowledgeId === knowledgeId) setEditingKnowledgeId('')
      await loadKnowledge()
    } catch (err) {
      onMessage(err.message || '停用失败', 'error')
    }
  }

  async function handleSaveBinding() {
    if (!selectedId || !bindingForm.knowledge_id) {
      onMessage('请选择 Knowledge', 'error')
      return
    }
    try {
      await admin.saveIndependentAgentBinding(selectedId, bindingForm)
      onMessage('Binding 已保存', 'success')
      setBindingForm(emptyBindingForm())
      await loadDetail(selectedId)
    } catch (err) {
      onMessage(err.message || '保存 Binding 失败', 'error')
    }
  }

  async function handleDeleteBinding(bindingId) {
    if (!window.confirm('确认删除该 Binding？')) return
    try {
      await admin.deleteIndependentAgentBinding(selectedId, bindingId)
      onMessage('Binding 已删除', 'success')
      await loadDetail(selectedId)
    } catch (err) {
      onMessage(err.message || '删除 Binding 失败', 'error')
    }
  }

  if (loading) return <AdminLoading label="加载独立 Agent…" />

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <div className="space-y-2">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Agent 列表</h3>
          <button type="button" onClick={loadAgents} className="text-navy-300 hover:text-white">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        {agents.length ? (
          agents.map((agent) => (
            <button
              key={agent.agent_id}
              type="button"
              onClick={() => setSelectedId(agent.agent_id)}
              className={cn(
                'w-full rounded-xl border px-3 py-3 text-left transition',
                selectedId === agent.agent_id
                  ? 'border-gold-400/40 bg-gold-400/10'
                  : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]',
              )}
            >
              <div className="text-sm font-medium text-white">{agent.name_zh || agent.name}</div>
              <div className="mt-1 text-xs text-navy-400">{agent.agent_id}</div>
              <div className="mt-2">
                <AdminHealthBadges health={agent.health} />
              </div>
            </button>
          ))
        ) : (
          <AdminEmpty title="暂无 Agent" />
        )}
      </div>

      {detail ? (
        <div className="space-y-5 rounded-2xl border border-white/10 bg-slate-900/40 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-white">{detail.name_zh || detail.name}</h2>
              <p className="mt-1 text-sm text-navy-300">{detail.description}</p>
              <div className="mt-3">
                <AdminHealthBadges health={detail.health} />
              </div>
              {!detail.health?.route_ok ? (
                <p className="mt-2 text-xs text-amber-200">
                  缺少 LLM Provider 时 C 端不可运行。请前往
                  <Link to="/admin/agent?tab=routes" className="mx-1 text-gold-300 underline">
                    路由
                  </Link>
                  配置或执行 seed。
                </p>
              ) : null}
            </div>
            <button
              type="button"
              disabled={saving}
              onClick={handleSave}
              className={adminBtnPrimary()}
            >
              <Save className="h-4 w-4" />
              保存
            </button>
          </div>

          <AdminTabBar tabs={AGENT_DETAIL_TABS} active={detailTab} onChange={setDetailTab} stretch />

          {detailTab === 'overview' ? (
          <>
          <div className="grid gap-4 md:grid-cols-2">
            <label className={labelCls}>
              中文名
              <input
                className={inputCls}
                value={detail.name_zh || ''}
                onChange={(e) => setDetail({ ...detail, name_zh: e.target.value })}
              />
            </label>
            <label className={labelCls}>
              启用
              <select
                className={inputCls}
                value={detail.is_enabled ? '1' : '0'}
                onChange={(e) => setDetail({ ...detail, is_enabled: e.target.value === '1' })}
              >
                <option value="1">启用</option>
                <option value="0">停用</option>
              </select>
            </label>
          </div>

          <label className={labelCls}>
            描述
            <textarea
              className={cn(inputCls, 'min-h-[72px]')}
              value={detail.description || ''}
              onChange={(e) => setDetail({ ...detail, description: e.target.value })}
            />
          </label>
          </>
          ) : null}

          {detailTab === 'contracts' ? (
          <div className="grid gap-4 lg:grid-cols-3">
            <label className={labelCls}>
              input_contract
              <textarea className={cn(inputCls, 'min-h-[160px] font-mono text-xs')} value={inputContractText} onChange={(e) => setInputContractText(e.target.value)} />
            </label>
            <label className={labelCls}>
              output_contract
              <textarea className={cn(inputCls, 'min-h-[160px] font-mono text-xs')} value={outputContractText} onChange={(e) => setOutputContractText(e.target.value)} />
            </label>
            <label className={labelCls}>
              runtime_policy
              <textarea className={cn(inputCls, 'min-h-[160px] font-mono text-xs')} value={runtimePolicyText} onChange={(e) => setRuntimePolicyText(e.target.value)} />
            </label>
          </div>
          ) : null}

          {detailTab === 'prompt' ? (
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Prompt 版本</h3>
              <button type="button" onClick={() => openPromptEditor(null)} className="text-xs text-gold-300">
                <Plus className="mr-1 inline h-3 w-3" />
                新建版本
              </button>
            </div>
            <div className="space-y-2">
              {prompts.map((prompt) => (
                <div
                  key={prompt.id}
                  className="flex items-center justify-between rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
                >
                  <div>
                    <button type="button" onClick={() => openPromptEditor(prompt)} className="text-white hover:text-gold-200">
                      {prompt.version}
                    </button>
                    {prompt.is_active ? <span className="ml-2 text-xs text-green-300">active</span> : null}
                    {prompt.change_notes ? <p className="mt-1 text-xs text-navy-400">{prompt.change_notes}</p> : null}
                  </div>
                  {!prompt.is_active ? (
                    <button type="button" onClick={() => handleActivatePrompt(prompt.version)} className="text-xs text-gold-300">
                      激活
                    </button>
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                  )}
                </div>
              ))}
            </div>
            <PromptVersionDiff prompts={prompts} />
            {editingPromptVersion !== '' || promptForm.version ? (
              <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/20 p-4">
                <h4 className="text-sm font-medium text-white">编辑 Prompt：{promptForm.version || '新版本'}</h4>
                <label className={labelCls}>
                  版本号
                  <input className={inputCls} value={promptForm.version} onChange={(e) => setPromptForm({ ...promptForm, version: e.target.value })} />
                </label>
                <label className={labelCls}>
                  system_prompt
                  <textarea className={cn(inputCls, 'min-h-[100px] font-mono text-xs')} value={promptForm.system_prompt} onChange={(e) => setPromptForm({ ...promptForm, system_prompt: e.target.value })} />
                </label>
                <label className={labelCls}>
                  user_prompt_template
                  <textarea className={cn(inputCls, 'min-h-[120px] font-mono text-xs')} value={promptForm.user_prompt_template} onChange={(e) => setPromptForm({ ...promptForm, user_prompt_template: e.target.value })} />
                </label>
                <label className={labelCls}>
                  output_format_prompt
                  <textarea className={cn(inputCls, 'min-h-[80px] font-mono text-xs')} value={promptForm.output_format_prompt} onChange={(e) => setPromptForm({ ...promptForm, output_format_prompt: e.target.value })} />
                </label>
                <label className={labelCls}>
                  constraints_prompt
                  <textarea className={cn(inputCls, 'min-h-[80px] font-mono text-xs')} value={promptForm.constraints_prompt} onChange={(e) => setPromptForm({ ...promptForm, constraints_prompt: e.target.value })} />
                </label>
                <label className={labelCls}>
                  change_notes
                  <input className={inputCls} value={promptForm.change_notes} onChange={(e) => setPromptForm({ ...promptForm, change_notes: e.target.value })} />
                </label>
                <button type="button" onClick={handleSavePrompt} className="rounded-lg bg-gold-400 px-3 py-1.5 text-xs font-medium text-navy-950">
                  保存 Prompt
                </button>
              </div>
            ) : null}
          </div>
          ) : null}

          {detailTab === 'knowledge' ? (
          <>
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Knowledge 库</h3>
              <button type="button" onClick={() => openKnowledgeEditor('')} className="text-xs text-gold-300">
                <Plus className="mr-1 inline h-3 w-3" />
                新建
              </button>
            </div>
            <input
              className={cn(inputCls, 'mb-3')}
              placeholder="搜索 knowledge_id / title / category"
              value={knowledgeQuery}
              onChange={(e) => setKnowledgeQuery(e.target.value)}
            />
            <div className="max-h-40 space-y-1 overflow-y-auto">
              {filteredKnowledge.map((row) => (
                <div key={row.id} className="flex items-center justify-between rounded-lg border border-white/5 bg-black/10 px-3 py-2 text-xs">
                  <button type="button" onClick={() => openKnowledgeEditor(row.knowledge_id)} className="text-left text-navy-100 hover:text-white">
                    <span className="font-medium">{row.title || row.knowledge_id}</span>
                    <span className="ml-2 text-navy-500">{row.knowledge_id}</span>
                  </button>
                  <button type="button" onClick={() => handleDeleteKnowledge(row.knowledge_id)} className="text-red-300">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
            {editingKnowledgeId ? (
              <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/20 p-4">
                <h4 className="text-sm font-medium text-white">编辑 Knowledge</h4>
                <label className={labelCls}>
                  knowledge_id
                  <input className={inputCls} disabled={editingKnowledgeId !== '__new__'} value={knowledgeForm.knowledge_id} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, knowledge_id: e.target.value })} />
                </label>
                <label className={labelCls}>
                  title
                  <input className={inputCls} value={knowledgeForm.title} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, title: e.target.value })} />
                </label>
                <label className={labelCls}>
                  content_text
                  <textarea className={cn(inputCls, 'min-h-[120px] font-mono text-xs')} value={knowledgeForm.content_text} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, content_text: e.target.value })} />
                </label>
                <button type="button" onClick={handleSaveKnowledge} className="rounded-lg bg-gold-400 px-3 py-1.5 text-xs font-medium text-navy-950">
                  保存 Knowledge
                </button>
              </div>
            ) : null}
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-white">Knowledge 绑定</h3>
            {bindings.length ? (
              <div className="mb-3 space-y-2">
                {bindings.map((row) => (
                  <div key={row.id} className="flex items-center justify-between rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-navy-200">
                    <div>
                      <div className="font-medium text-white">{row.knowledge_title || row.knowledge_id}</div>
                      <div className="mt-1 text-navy-400">
                        {row.binding_type} · {row.inject_position} · order {row.order_index}
                      </div>
                    </div>
                    <button type="button" onClick={() => handleDeleteBinding(row.id)} className="text-red-300">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mb-3 text-xs text-navy-400">暂无绑定</p>
            )}
            <div className="grid gap-3 rounded-xl border border-white/10 bg-black/20 p-4 md:grid-cols-2">
              <label className={labelCls}>
                Knowledge
                <select className={inputCls} value={bindingForm.knowledge_id} onChange={(e) => setBindingForm({ ...bindingForm, knowledge_id: e.target.value })}>
                  <option value="">选择…</option>
                  {knowledgeRows.map((row) => (
                    <option key={row.id} value={row.knowledge_id}>
                      {row.title || row.knowledge_id}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelCls}>
                binding_type
                <select className={inputCls} value={bindingForm.binding_type} onChange={(e) => setBindingForm({ ...bindingForm, binding_type: e.target.value })}>
                  <option value="required">required</option>
                  <option value="optional">optional</option>
                  <option value="validator">validator</option>
                </select>
              </label>
              <label className={labelCls}>
                inject_position
                <select className={inputCls} value={bindingForm.inject_position} onChange={(e) => setBindingForm({ ...bindingForm, inject_position: e.target.value })}>
                  <option value="context">context</option>
                  <option value="system">system</option>
                  <option value="user">user</option>
                </select>
              </label>
              <label className={labelCls}>
                order_index
                <input type="number" className={inputCls} value={bindingForm.order_index} onChange={(e) => setBindingForm({ ...bindingForm, order_index: Number(e.target.value) })} />
              </label>
              <button type="button" onClick={handleSaveBinding} className="rounded-lg bg-gold-400 px-3 py-1.5 text-xs font-medium text-navy-950 md:col-span-2">
                添加/更新 Binding
              </button>
            </div>
          </div>
          </>
          ) : null}

          {detailTab === 'runs' ? (
          <div>
            <h3 className="mb-3 text-sm font-semibold text-white">最近运行</h3>
            {recentRuns.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-navy-200">
                  <thead>
                    <tr className="border-b border-white/10 text-navy-400">
                      <th className="py-2 pr-3">时间</th>
                      <th className="py-2 pr-3">状态</th>
                      <th className="py-2 pr-3">tokens</th>
                      <th className="py-2 pr-3">成本(元)</th>
                      <th className="py-2">项目</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentRuns.map((run) => (
                      <tr key={run.id} className="border-b border-white/5">
                        <td className="py-2 pr-3">{run.started_at?.slice(0, 16) || '-'}</td>
                        <td className="py-2 pr-3">{run.status}</td>
                        <td className="py-2 pr-3">{run.total_tokens ?? run.estimated_prompt_tokens ?? '-'}</td>
                        <td className="py-2 pr-3">{(run.estimated_cost_yuan ?? 0).toFixed(4)}</td>
                        <td className="py-2">
                          {run.project_id ? (
                            <AdminPenetrationLink
                              to={adminProjectDetailPath(run.project_id, 'runs')}
                              label={run.project_title || String(run.project_id).slice(0, 8)}
                            />
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-navy-400">暂无运行记录</p>
            )}
          </div>
          ) : null}
        </div>
      ) : (
        <AdminEmpty title="选择左侧 Agent 查看详情" />
      )}
    </div>
  )
}

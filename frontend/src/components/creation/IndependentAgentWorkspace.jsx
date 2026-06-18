import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  ArrowLeft,
  Check,
  Download,
  History,
  Loader2,
  Play,
  Share2,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { creation } from '@/services/api'
import { cn } from '@/utils/cn'
import ArtifactPreviewPanel from './ArtifactPreviewPanel'

function healthReasons(agent) {
  const reasons = []
  const health = agent?.health || {}
  if (agent?.missing_inputs?.length) {
    reasons.push(`缺少输入产物：${agent.missing_inputs.join('、')}`)
  }
  if (!health.prompt_ok) reasons.push('缺少可用 Prompt 版本')
  if (!health.route_ok) reasons.push('缺少 LLM 路由或 Provider，请联系管理员配置')
  if (!health.contract_ok) reasons.push('输入/输出契约不完整')
  if (health.healthy === false && !reasons.length) reasons.push('Agent 暂不可运行')
  return reasons
}

function defaultParams(agent, episodeCount = 80) {
  const schema = agent?.ui_schema?.params || []
  const params = {}
  for (const field of schema) {
    if (field.key === 'episode_from') params.episode_from = field.default ?? 1
    else if (field.key === 'episode_to') params.episode_to = field.default ?? Math.min(3, episodeCount)
    else if (field.key === 'overwrite') params.overwrite = field.default ?? 'merge'
    else if (field.default !== undefined) params[field.key] = field.default
  }
  return params
}

function AgentStatusBadge({ agent }) {
  const status = agent?.latest_run?.status
  if (!agent?.enabled) return <span className="text-xs text-slate-400">已停用</span>
  if (status === 'running') return <span className="text-xs text-gold-300">运行中</span>
  if (status === 'failed') return <span className="text-xs text-red-300">失败</span>
  if (agent?.has_output) return <span className="text-xs text-green-300">已有产物</span>
  if (agent?.missing_inputs?.length) return <span className="text-xs text-slate-400">缺少输入</span>
  if (!agent?.can_run) return <span className="text-xs text-amber-200">不可运行</span>
  return <span className="text-xs text-blue-200">可运行</span>
}

function AgentParamsForm({ agent, episodeCount, value, onChange }) {
  const fields = agent?.ui_schema?.params || []
  if (!fields.length) return null

  return (
    <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
      <h3 className="text-sm font-medium text-white">运行参数</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {fields.map((field) => {
          const key = field.key
          if (field.type === 'select') {
            return (
              <label key={key} className="block text-xs text-navy-300">
                {field.label || key}
                <select
                  className="mt-1 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
                  value={value[key] ?? field.default ?? ''}
                  onChange={(e) => onChange({ ...value, [key]: e.target.value })}
                >
                  {(field.options || []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label || opt.value}
                    </option>
                  ))}
                </select>
              </label>
            )
          }
          return (
            <label key={key} className="block text-xs text-navy-300">
              {field.label || key}
              <input
                type="number"
                min={field.min ?? 1}
                max={key.includes('episode') ? episodeCount : undefined}
                className="mt-1 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
                value={value[key] ?? field.default ?? ''}
                onChange={(e) => onChange({ ...value, [key]: Number(e.target.value) })}
              />
            </label>
          )
        })}
      </div>
    </div>
  )
}

function RunDetailDrawer({ run, loading, onClose }) {
  if (!run && !loading) return null
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50">
      <div className="h-full w-full max-w-lg overflow-y-auto border-l border-white/10 bg-slate-950 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">运行详情</h3>
          <button type="button" onClick={onClose} className="text-navy-300 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 text-navy-300">
            <Loader2 className="h-4 w-4 animate-spin" />
            加载中…
          </div>
        ) : (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-2 text-navy-300">
              <span>状态</span>
              <span className="text-white">{run.status}</span>
              <span>批次</span>
              <span className="text-white">
                {run.batch_from || '-'} – {run.batch_to || '-'}
              </span>
              <span>预计 tokens</span>
              <span className="text-white">{run.estimated_prompt_tokens ?? '-'}</span>
              <span>实际 tokens</span>
              <span className="text-white">{run.total_tokens ?? '-'}</span>
              <span>模型</span>
              <span className="text-white">{run.model_name || '-'}</span>
            </div>
            {run.error_message ? (
              <div className="rounded-lg border border-red-400/20 bg-red-500/10 p-3 text-red-100">
                {run.error_message}
              </div>
            ) : null}
            {run.run_params && Object.keys(run.run_params).length ? (
              <div>
                <h4 className="mb-2 font-medium text-white">运行参数</h4>
                <pre className="max-h-40 overflow-auto rounded-lg bg-black/30 p-3 text-xs text-navy-100">
                  {JSON.stringify(run.run_params, null, 2)}
                </pre>
              </div>
            ) : null}
            {run.input_artifact_keys?.length ? (
              <div>
                <h4 className="mb-2 font-medium text-white">输入产物</h4>
                <p className="text-navy-300">{run.input_artifact_keys.join('、')}</p>
              </div>
            ) : null}
            {run.input_snapshot && Object.keys(run.input_snapshot).length ? (
              <div>
                <h4 className="mb-2 font-medium text-white">输入摘要</h4>
                <div className="space-y-2 text-xs text-navy-300">
                  {(run.input_snapshot.input_artifact_keys || run.input_artifact_keys || []).length ? (
                    <p>
                      输入产物：
                      {(run.input_snapshot.input_artifact_keys || run.input_artifact_keys || []).join('、')}
                    </p>
                  ) : null}
                  {run.input_snapshot.params && Object.keys(run.input_snapshot.params).length ? (
                    <pre className="max-h-32 overflow-auto rounded-lg bg-black/30 p-3 text-navy-100">
                      {JSON.stringify(run.input_snapshot.params, null, 2)}
                    </pre>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}

function formatTokenLimitLabel(agent, tokenEstimate, isActive) {
  if (isActive && tokenEstimate?.estimated_prompt_tokens != null) {
    const maxPrompt =
      tokenEstimate.max_prompt_tokens || agent.token_policy?.max_prompt_tokens || '-'
    return `预估 ${tokenEstimate.estimated_prompt_tokens} / ${maxPrompt} tokens`
  }
  const promptMax = agent.token_policy?.max_prompt_tokens
  const completionMax = agent.token_policy?.max_completion_tokens
  if (promptMax != null && completionMax != null) {
    return `输入上限 ${promptMax} · 输出上限 ${completionMax} tokens`
  }
  return 'Token 上限未配置'
}

function formatCharCount(chars) {
  if (!chars) return '0'
  if (chars >= 1000) return `${(chars / 1000).toFixed(1)}k`
  return String(chars)
}

function AgentCard({ agent, active, busy, projectLocked, tokenEstimate, onSelect, onRun }) {
  const overLimit = tokenEstimate && tokenEstimate.within_limit === false
  const disabled = busy || projectLocked || !agent.can_run || overLimit
  const reasons = !agent.can_run ? healthReasons(agent) : []
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'w-full rounded-2xl border p-4 text-left transition',
        active ? 'border-gold-400/60 bg-gold-400/10' : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">{agent.name_zh || agent.name}</h3>
          <p className="mt-1 text-xs text-navy-300">{agent.agent_id}</p>
        </div>
        <AgentStatusBadge agent={agent} />
      </div>
      <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-navy-300">{agent.description}</p>
      {reasons.slice(0, 2).map((line) => (
        <p key={line} className="mt-2 text-xs text-amber-200">
          {line}
        </p>
      ))}
      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-navy-400">
        {(agent.output_artifacts || []).map((key) => (
          <span key={key} className="rounded-full bg-white/[0.05] px-2 py-1">
            输出 {key}
          </span>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <span
          className={cn(
            'text-[11px]',
            overLimit ? 'text-red-300' : 'text-navy-500',
          )}
        >
          {formatTokenLimitLabel(agent, tokenEstimate, active)}
        </span>
        <span
          role="button"
          tabIndex={0}
          onClick={(event) => {
            event.stopPropagation()
            if (!disabled) onRun(agent)
          }}
          className={cn(
            'inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium',
            disabled
              ? 'cursor-not-allowed bg-white/[0.05] text-slate-500'
              : 'bg-gold-400 text-navy-950 hover:bg-gold-300',
          )}
        >
          {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
          运行
        </span>
      </div>
    </button>
  )
}

export default function IndependentAgentWorkspace({ projectId, onBack, onRestart }) {
  const [workspace, setWorkspace] = useState(null)
  const [activeAgentId, setActiveAgentId] = useState('')
  const [artifactMap, setArtifactMap] = useState({})
  const [activeArtifactKey, setActiveArtifactKey] = useState('')
  const [agentParams, setAgentParams] = useState({})
  const [runHistory, setRunHistory] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [runDetailLoading, setRunDetailLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [runningAgentId, setRunningAgentId] = useState('')
  const [downloadingFormat, setDownloadingFormat] = useState('')
  const [sharing, setSharing] = useState(false)
  const [error, setError] = useState('')
  const [tokenEstimate, setTokenEstimate] = useState(null)
  const [estimateLoading, setEstimateLoading] = useState(false)

  const agents = workspace?.agents || []
  const episodeCount = workspace?.project?.episode_count || 80
  const projectLocked = Boolean(
    workspace?.project?.has_running_agent ||
      agents.some((agent) => agent.latest_run?.status === 'running'),
  )

  const activeAgent = useMemo(
    () => agents.find((agent) => agent.agent_id === activeAgentId) || agents[0],
    [agents, activeAgentId],
  )

  const outputKeys = activeAgent?.output_artifacts || []
  const activeArtifact = activeArtifactKey ? artifactMap[activeArtifactKey] : null

  const loadWorkspace = useCallback(async () => {
    if (!projectId) return
    try {
      const data = await creation.workspace(projectId)
      setWorkspace(data)
      setError('')
      setActiveAgentId((prev) => prev || data?.agents?.[0]?.agent_id || '')
    } catch (err) {
      setError(err.message || '加载工作台失败')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    loadWorkspace()
  }, [loadWorkspace])

  useEffect(() => {
    if (!projectLocked) return
    const timer = window.setInterval(loadWorkspace, 3000)
    return () => window.clearInterval(timer)
  }, [loadWorkspace, projectLocked])

  useEffect(() => {
    if (!activeAgent) return
    setAgentParams(defaultParams(activeAgent, episodeCount))
    const firstKey = activeAgent.output_artifacts?.[0] || ''
    setActiveArtifactKey(firstKey)
  }, [activeAgent?.agent_id, episodeCount])

  useEffect(() => {
    if (!activeAgent?.can_run || !projectId) {
      setTokenEstimate(null)
      return undefined
    }
    let cancelled = false
    const timer = window.setTimeout(async () => {
      setEstimateLoading(true)
      try {
        const data = await creation.estimateAgent(projectId, activeAgent.agent_id, agentParams)
        if (!cancelled) setTokenEstimate(data)
      } catch {
        if (!cancelled) setTokenEstimate(null)
      } finally {
        if (!cancelled) setEstimateLoading(false)
      }
    }, 400)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [activeAgent?.agent_id, activeAgent?.can_run, agentParams, projectId])

  useEffect(() => {
    let cancelled = false
    async function loadRuns() {
      if (!projectId || !activeAgent?.agent_id) {
        if (!cancelled) setRunHistory([])
        return
      }
      try {
        const rows = await creation.agentRuns(projectId, activeAgent.agent_id)
        if (!cancelled) {
          setRunHistory(Array.isArray(rows) ? rows : rows?.runs || [])
        }
      } catch {
        if (!cancelled) setRunHistory([])
      }
    }
    loadRuns()
    return () => {
      cancelled = true
    }
  }, [activeAgent?.agent_id, projectId, workspace])

  useEffect(() => {
    let cancelled = false
    async function loadArtifacts() {
      if (!projectId || !activeAgent) {
        if (!cancelled) setArtifactMap({})
        return
      }
      const keys = activeAgent.output_artifacts || []
      const entries = await Promise.all(
        keys.map(async (key) => {
          try {
            const data = await creation.artifact(projectId, key)
            return [key, data]
          } catch {
            return [key, null]
          }
        }),
      )
      if (cancelled) return
      const next = {}
      for (const [key, data] of entries) {
        if (data?.payload || data?.editor_view) next[key] = data
      }
      setArtifactMap(next)
      if (!activeArtifactKey && keys[0]) setActiveArtifactKey(keys[0])
    }
    loadArtifacts()
    return () => {
      cancelled = true
    }
  }, [activeAgent, projectId, workspace?.artifacts])

  async function handleRun(agent) {
    const params = agent.agent_id === activeAgent?.agent_id ? agentParams : defaultParams(agent, episodeCount)
    if (agent.agent_id === activeAgent?.agent_id && tokenEstimate?.within_limit === false) {
      toast.error('预计输入 tokens 超过上限，请调整参数或联系管理员')
      return
    }
    setRunningAgentId(agent.agent_id)
    try {
      const result = await creation.runAgent(projectId, agent.agent_id, params)
      if (result?.already_running) {
        toast.info('该 Agent 已在运行中')
      } else {
        toast.success(`${agent.name_zh || agent.agent_id} 已加入队列`)
      }
      await loadWorkspace()
    } catch (err) {
      toast.error(err.message || '运行失败')
    } finally {
      setRunningAgentId('')
    }
  }

  async function openRunDetail(runId) {
    setRunDetailLoading(true)
    setSelectedRun({ id: runId })
    try {
      const detail = await creation.runDetail(projectId, runId)
      setSelectedRun(detail)
    } catch (err) {
      toast.error(err.message || '加载运行详情失败')
      setSelectedRun(null)
    } finally {
      setRunDetailLoading(false)
    }
  }

  async function handleDownload(format) {
    setDownloadingFormat(format)
    try {
      const blob = await creation.download(projectId, format)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${workspace?.project?.title || 'scriptforge'}.${format}`
      link.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(err.message || '下载失败')
    } finally {
      setDownloadingFormat('')
    }
  }

  async function handleShare() {
    setSharing(true)
    try {
      const res = await creation.share(projectId, { allow_download: false })
      const url = res?.share_url || res?.url || ''
      if (url) await navigator.clipboard.writeText(url)
      toast.success(url ? '分享链接已复制' : '分享链接已生成')
    } catch (err) {
      toast.error(err.message || '生成分享链接失败')
    } finally {
      setSharing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center text-navy-300">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        加载独立 Agent 工作台…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-6 text-red-100">
        <AlertCircle className="mb-3 h-6 w-6" />
        <p>{error}</p>
        <button type="button" onClick={onRestart} className="mt-4 text-sm text-gold-300">
          重新开始
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <RunDetailDrawer
        run={selectedRun}
        loading={runDetailLoading}
        onClose={() => setSelectedRun(null)}
      />

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <button type="button" onClick={onBack} className="mb-3 inline-flex items-center gap-2 text-sm text-navy-300">
            <ArrowLeft className="h-4 w-4" />
            返回
          </button>
          <h1 className="text-2xl font-semibold text-white">{workspace?.project?.title || '项目工作台'}</h1>
          <p className="mt-1 text-sm text-navy-300">独立 Agent 手动运行，每次只读取已有项目数据并写入自己的产物。</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!workspace?.project?.can_download || Boolean(downloadingFormat)}
            onClick={() => handleDownload('md')}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-white disabled:opacity-40"
          >
            {downloadingFormat ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            下载
          </button>
          <button
            type="button"
            disabled={!workspace?.project?.can_share || sharing}
            onClick={handleShare}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-white disabled:opacity-40"
          >
            {sharing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Share2 className="h-4 w-4" />}
            分享
          </button>
        </div>
      </div>

      {projectLocked ? (
        <div className="mb-4 rounded-xl border border-gold-400/30 bg-gold-400/10 px-4 py-3 text-sm text-gold-100">
          项目有 Agent 正在运行，请等待完成后再启动新的运行。
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-3">
          {agents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              active={agent.agent_id === activeAgent?.agent_id}
              busy={runningAgentId === agent.agent_id}
              projectLocked={projectLocked}
              tokenEstimate={agent.agent_id === activeAgent?.agent_id ? tokenEstimate : null}
              onSelect={() => setActiveAgentId(agent.agent_id)}
              onRun={handleRun}
            />
          ))}
        </div>

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
          {activeAgent ? (
            <>
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">{activeAgent.name_zh || activeAgent.name}</h2>
                  <p className="mt-1 text-sm text-navy-300">{activeAgent.description}</p>
                </div>
                {activeAgent.has_output ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-400/10 px-3 py-1 text-xs text-green-300">
                    <Check className="h-3 w-3" />
                    已输出
                  </span>
                ) : null}
              </div>

              {!activeAgent.can_run ? (
                <div className="mb-5 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4">
                  <h3 className="text-sm font-medium text-amber-100">暂不可运行</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-amber-50/90">
                    {healthReasons(activeAgent).map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <AgentParamsForm
                agent={activeAgent}
                episodeCount={episodeCount}
                value={agentParams}
                onChange={setAgentParams}
              />

              {tokenEstimate ? (
                <div
                  className={cn(
                    'mt-4 rounded-2xl border p-4 text-sm',
                    tokenEstimate.within_limit === false
                      ? 'border-red-400/30 bg-red-500/10 text-red-100'
                      : 'border-white/10 bg-black/10 text-navy-200',
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span>
                      预估输入 tokens：
                      <strong className="text-white">{tokenEstimate.estimated_prompt_tokens ?? '-'}</strong>
                      {' / '}
                      {tokenEstimate.max_prompt_tokens || activeAgent.token_policy?.max_prompt_tokens || '-'}
                    </span>
                    {estimateLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  </div>
                  {tokenEstimate.input_char_summary && Object.keys(tokenEstimate.input_char_summary).length ? (
                    <p className="mt-2 text-xs opacity-80">
                      输入体量：
                      {Object.entries(tokenEstimate.input_char_summary)
                        .map(([key, chars]) => `${key} ${formatCharCount(chars)} chars`)
                        .join(' · ')}
                    </p>
                  ) : null}
                </div>
              ) : null}

              <div className="mb-5 mt-5 grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
                  <h3 className="text-sm font-medium text-white">输入要求</h3>
                  <ul className="mt-2 space-y-1 text-sm">
                    {(activeAgent.required_inputs || []).length ? (
                      activeAgent.required_inputs.map((key) => {
                        const missing = (activeAgent.missing_inputs || []).includes(key)
                        return (
                          <li
                            key={key}
                            className={cn(missing ? 'text-amber-200' : 'text-green-300')}
                          >
                            {missing ? '○' : '●'} {key}
                          </li>
                        )
                      })
                    ) : (
                      <li className="text-navy-300">仅项目基础字段</li>
                    )}
                  </ul>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
                  <h3 className="text-sm font-medium text-white">输出产物</h3>
                  <p className="mt-2 text-sm text-navy-300">
                    {(activeAgent.output_artifacts || []).join('、') || '-'}
                  </p>
                  <button
                    type="button"
                    disabled={
                      projectLocked ||
                      !activeAgent.can_run ||
                      tokenEstimate?.within_limit === false
                    }
                    onClick={() => handleRun(activeAgent)}
                    className="mt-3 inline-flex items-center gap-2 rounded-lg bg-gold-400 px-4 py-2 text-sm font-medium text-navy-950 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-500"
                  >
                    {runningAgentId === activeAgent.agent_id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    运行此 Agent
                  </button>
                </div>
              </div>

              <div className="mb-5 rounded-2xl border border-white/10 bg-black/10 p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
                  <History className="h-4 w-4" />
                  运行历史
                </div>
                {runHistory.length ? (
                  <div className="space-y-2">
                    {runHistory.slice(0, 8).map((run) => (
                      <button
                        key={run.id}
                        type="button"
                        onClick={() => openRunDetail(run.id)}
                        className="flex w-full items-center justify-between rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-left text-xs text-navy-200 hover:bg-white/[0.04]"
                      >
                        <span>
                          {run.status} · {run.started_at?.slice(0, 16) || '-'}
                        </span>
                        <span className="text-navy-500">{run.total_tokens ?? run.estimated_prompt_tokens ?? '-'} tok</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-navy-400">暂无运行记录</p>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <h3 className="mb-3 text-sm font-medium text-white">Artifact 预览</h3>
                {outputKeys.length > 1 ? (
                  <div className="mb-3 flex flex-wrap gap-2">
                    {outputKeys.map((key) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setActiveArtifactKey(key)}
                        className={cn(
                          'rounded-lg px-3 py-1.5 text-xs',
                          activeArtifactKey === key
                            ? 'bg-gold-400/20 text-gold-200'
                            : 'bg-white/[0.05] text-navy-300',
                        )}
                      >
                        {key}
                      </button>
                    ))}
                  </div>
                ) : null}
                {activeArtifact?.editor_view || activeArtifact?.payload ? (
                  <ArtifactPreviewPanel
                    editorView={
                      activeArtifact.editor_view || {
                        mode: 'json',
                        payload: activeArtifact.payload,
                      }
                    }
                  />
                ) : (
                  <p className="text-sm text-navy-400">当前 Agent 尚无可预览产物。</p>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-navy-400">暂无可用 Agent，请先在后台初始化 Agent 配置。</p>
          )}
        </section>
      </div>
    </div>
  )
}

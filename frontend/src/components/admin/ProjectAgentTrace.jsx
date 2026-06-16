import { useCallback, useEffect, useState } from 'react'
import { GitBranch, Layers, ShieldCheck } from 'lucide-react'
import ExecutionRunPanel from '@/components/shared/ExecutionRunPanel'
import AgentTimelineCard from '@/components/admin/AgentTimelineCard'
import { SubSkillLegend } from '@/components/admin/SubSkillStepBar'
import CreationPipelineDiagram from '@/components/admin/CreationPipelineDiagram'
import { AdminTabBar } from '@/components/admin/AdminUI'
import ProjectOpsSummary, {
  ProjectFusionNodesPanel,
  ProjectVerifyPanel,
} from '@/components/admin/ProjectOpsSummary'
import { resolveAgentDisplayName } from '@/utils/agentExecutionLabels'
import { resolveSkillId } from '@/utils/skillTerm'
import { admin } from '@/services/api'

const POST_CHAIN_ORDER = ['review', 'polish', 'score', 'marketing', 'insight']

const TRACE_TABS = [
  { key: 'timeline', label: 'Agent 轨迹', icon: GitBranch },
  { key: 'nodes', label: '融合节点', icon: Layers },
  { key: 'verify', label: '原创复核', icon: ShieldCheck },
]

export function agentDisplayName(agentKey, catalog, entry) {
  const id = resolveSkillId(entry) || agentKey
  if (id === 'adapt') return '改编预处理'
  const nodeIndex = Number.isFinite(Number(agentKey)) ? Number(agentKey) : entry?.node_index
  return resolveAgentDisplayName(id, catalog, nodeIndex)
}

export function useProjectTrace(projectId) {
  const [catalog, setCatalog] = useState(null)
  const [traceData, setTraceData] = useState(null)
  const [blueprint, setBlueprint] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    const id = (projectId || '').trim()
    if (!id) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    try {
      const [cat, traces, bp] = await Promise.all([
        admin.agentCatalog().catch(() => null),
        admin.agentProjectTraces(id),
        admin.getMainChainBlueprint().catch(() => null),
      ])
      setCatalog(cat)
      setTraceData(traces)
      setBlueprint(bp)
    } catch (e) {
      setTraceData(null)
      setError(e.message || '加载轨迹失败')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    load()
  }, [load])

  return { catalog, traceData, blueprint, loading, error, reload: load }
}

export function ProjectTracePanel({
  traceData,
  catalog,
  traces,
  blueprint = null,
  latestRuns = {},
  onInspectRun,
  compact = false,
}) {
  const orderedKeys = (() => {
    const keys = Object.keys(traces || {})
    const workspace = (catalog?.workspaceAgents || [])
      .map((a) => String(a.workspace_index))
      .filter((k) => keys.includes(k))
    const adapt = keys.includes('adapt') ? ['adapt'] : []
    const post = POST_CHAIN_ORDER.filter((k) => keys.includes(k))
    const rest = keys.filter((k) => !workspace.includes(k) && k !== 'adapt' && !post.includes(k))
    return [...adapt, ...workspace, ...post, ...rest]
  })()

  const runLimit = compact ? 3 : 12
  const hasAdaptMeta = Boolean(traceData.adaptation_meta?.creationEntry)
  const showAdapt = hasAdaptMeta || traces.adapt

  return (
    <div className="space-y-4">
      {!compact ? (
        <CreationPipelineDiagram compact blueprint={blueprint} linkTo="/admin/orchestration?tab=flow" />
      ) : null}

      {traceData?.pipeline_mode ? (
        <div
          className={`rounded-xl border px-4 py-3 text-xs leading-relaxed ${
            traceData.pipeline_mode === 'workspace'
              ? 'border-white/10 bg-slate-900/40 text-navy-400'
              : 'border-violet-500/20 bg-violet-500/5 text-violet-200/80'
          }`}
        >
          {traceData.pipeline_mode === 'workspace' ? (
            <>
              <span className="font-medium text-navy-200">技能工作台</span>
              ：质检/评分等后处理在剧本全量生成后由 post_script_chain 统一执行，轨迹中可能以 review / score 等 agent 键出现。
            </>
          ) : (
            <>
              <span className="font-medium text-violet-100">分步掌控</span>
              ：节点 6/7 为管线尾部（fusion_review / fusion_score），与调度中心「流程编排」配置一致。
            </>
          )}
        </div>
      ) : null}

      <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
        <p className="text-sm text-navy-200 mb-2">
          按创作流水线顺序展示每个 Agent 的子技能步骤。绿色=已执行，红色=失败，灰色=跳过，虚线=尚未跑到。
        </p>
        <SubSkillLegend />
      </div>

      {showAdapt ? (
        <AgentTimelineCard
          title="改编预处理"
          subtitle={
            traceData.adaptation_meta?.creationEntry
              ? `入口 ${traceData.adaptation_meta.creationEntry}${
                  traceData.adaptation_meta.referenceWork
                    ? ` · 参考 ${traceData.adaptation_meta.referenceWork}`
                    : ''
                }`
              : 'adapt'
          }
          agentId="adapt"
          catalog={catalog}
          executionTrace={(traces.adapt || {}).execution_trace}
          dbRun={latestRuns.adapt}
          onInspectRun={onInspectRun}
        />
      ) : null}

      {orderedKeys
        .filter((key) => key !== 'adapt')
        .map((agentKey) => {
          const entry = traces[agentKey] || {}
          const agentId = resolveSkillId(entry) || agentKey
          const dbRun = latestRuns[agentKey] || latestRuns[resolveSkillId(entry)]
          const wsAgent = (catalog?.workspaceAgents || []).find(
            (a) => String(a.workspace_index) === String(agentKey),
          )
          const subtitle = wsAgent
            ? `${wsAgent.name || agentId} · 步骤 ${wsAgent.workspace_index}`
            : agentId

          return (
            <AgentTimelineCard
              key={agentKey}
              title={agentDisplayName(agentKey, catalog, entry)}
              subtitle={subtitle}
              agentId={agentId}
              catalog={catalog}
              executionTrace={entry.execution_trace}
              dbRun={dbRun}
              onInspectRun={onInspectRun}
            />
          )
        })}

      {!orderedKeys.length && !showAdapt ? (
        <p className="text-sm text-navy-400 py-8 text-center">该项目尚无 Agent 执行轨迹</p>
      ) : null}

      {(traceData.execution_runs || []).length > 0 ? (
        <details className="rounded-xl border border-white/5 bg-slate-900/40">
          <summary className="cursor-pointer px-4 py-3 text-sm text-white font-medium hover:bg-white/[0.06] rounded-xl">
            全部执行记录（{traceData.execution_runs.length} 条 DB 记录）
          </summary>
          <div className={`px-4 pb-4 space-y-2 ${compact ? 'max-h-[280px] overflow-y-auto' : ''}`}>
            {traceData.execution_runs.slice(0, runLimit).map((run) => (
              <button
                key={run.id}
                type="button"
                onClick={() => onInspectRun?.(run.id)}
                className="w-full text-left rounded-xl hover:ring-1 hover:ring-gold-500/30 transition"
              >
                <ExecutionRunPanel run={run} compact catalog={catalog} />
              </button>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  )
}

export function RunDetailModal({ runId, onClose }) {
  const [detail, setDetail] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    if (!runId) {
      setDetail(null)
      return undefined
    }
    setLoading(true)
    setLoadError('')
    Promise.all([
      admin.agentExecutionRun(runId),
      admin.agentCatalog().catch(() => null),
    ])
      .then(([runDetail, cat]) => {
        setDetail(runDetail)
        setCatalog(cat)
      })
      .catch((e) => {
        setDetail(null)
        setLoadError(e.message || '加载失败')
      })
      .finally(() => setLoading(false))
    return undefined
  }, [runId])

  if (!runId) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60">
      <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-900/95 p-5 shadow-2xl">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">执行详情</h3>
            {detail ? (
              <p className="text-sm text-gold-400/90 mt-1">
                {resolveAgentDisplayName(resolveSkillId(detail), catalog, detail.node_index)}
                {detail.node_index != null ? ` · 节点${detail.node_index}` : ''}
              </p>
            ) : null}
            <p className="text-xs text-navy-300 mt-1 font-mono">{runId}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-navy-400 hover:text-white px-3 py-1 rounded-lg border border-white/10"
          >
            关闭
          </button>
        </div>

        {loading ? <p className="text-sm text-navy-400">加载中…</p> : null}
        {loadError ? <p className="text-sm text-red-300">{loadError}</p> : null}

        {detail ? (
          <>
            <ExecutionRunPanel run={detail} catalog={catalog} />
            <div className="mt-4 rounded-xl border border-white/5 bg-slate-900/40 p-4">
              <p className="text-sm text-gold-400 mb-2">关联 LLM 调用</p>
              <p className="text-xs text-navy-400 mb-3">
                {detail.llm_summary?.call_count ?? 0} 次 ·{' '}
                {(detail.llm_summary?.total_tokens ?? 0).toLocaleString()} Token ·{' '}
                入 {(detail.llm_summary?.prompt_tokens ?? 0).toLocaleString()} / 出{' '}
                {(detail.llm_summary?.completion_tokens ?? 0).toLocaleString()} ·{' '}
                入 ¥{Number(detail.llm_summary?.estimated_input_cost_yuan || 0).toFixed(4)} / 出 ¥
                {Number(detail.llm_summary?.estimated_output_cost_yuan || 0).toFixed(4)} · 合计 ¥
                {Number(detail.llm_summary?.estimated_cost_yuan || 0).toFixed(4)}
              </p>
              {(detail.llm_usage || []).length ? (
                <ul className="space-y-2 text-xs">
                  {detail.llm_usage.map((row) => (
                    <li
                      key={row.id}
                      className="flex flex-wrap justify-between gap-2 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2 text-navy-200"
                    >
                      <span>
                        {row.sub_skill_id || row.source_key || '—'} · {row.model_name}
                      </span>
                      <span className="text-navy-400">
                        入 {row.prompt_tokens ?? 0} / 出 {row.completion_tokens ?? 0} · 入 ¥
                        {Number(row.estimated_input_cost_yuan || 0).toFixed(4)} / 出 ¥
                        {Number(row.estimated_output_cost_yuan || 0).toFixed(4)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-navy-400">本次执行无 LLM 用量记录</p>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

/** 完整项目监察视图：摘要 + Tab（轨迹 / 节点 / 复核） */
export function ProjectAgentTraceView({
  projectId,
  compact = false,
  activeTab = 'timeline',
  onTabChange,
  showSummary = true,
}) {
  const { catalog, traceData, blueprint, loading, error } = useProjectTrace(projectId)
  const [inspectRunId, setInspectRunId] = useState('')
  const tab = activeTab

  if (loading) {
    return <p className="text-sm text-navy-400 py-8 text-center">加载项目轨迹…</p>
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-red-300 text-sm">
        {error}
      </div>
    )
  }

  if (!traceData) {
    return <p className="text-sm text-navy-400">暂无轨迹数据</p>
  }

  const traces = traceData.execution_traces || {}

  return (
    <div className="space-y-4">
      <RunDetailModal runId={inspectRunId} onClose={() => setInspectRunId('')} />
      {showSummary ? <ProjectOpsSummary data={traceData} compact={compact} /> : null}

      {!compact && onTabChange ? (
        <AdminTabBar tabs={TRACE_TABS} active={tab} onChange={onTabChange} />
      ) : null}

      {tab === 'timeline' || compact ? (
        <ProjectTracePanel
          traceData={traceData}
          catalog={catalog}
          traces={traces}
          blueprint={blueprint}
          latestRuns={traceData.latest_execution_runs || {}}
          onInspectRun={setInspectRunId}
          compact={compact}
        />
      ) : null}

      {tab === 'nodes' && !compact ? (
        <ProjectFusionNodesPanel nodes={traceData.nodes} />
      ) : null}

      {tab === 'verify' && !compact ? (
        <ProjectVerifyPanel summary={traceData.verify_summary} />
      ) : null}
    </div>
  )
}

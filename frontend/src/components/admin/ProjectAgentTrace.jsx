import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, Layers, ShieldCheck, Package, AlertTriangle, Info } from 'lucide-react'
import ExecutionRunPanel from '@/components/shared/ExecutionRunPanel'
import { AdminTabBar } from '@/components/admin/AdminUI'
import ProjectOpsSummary, {
  ProjectVerifyPanel,
} from '@/components/admin/ProjectOpsSummary'
import { resolveAgentDisplayName } from '@/utils/agentExecutionLabels'
import { admin } from '@/services/api'

const DRAMA_EXEC_STATUS = {
  success: { label: '成功', tone: 'text-green-400 bg-green-500/10 border-green-500/20' },
  running: { label: '执行中', tone: 'text-blue-400 bg-blue-500/10 border-blue-500/20 animate-pulse' },
  failed: { label: '失败', tone: 'text-red-400 bg-red-500/10 border-red-500/20' },
  pending: { label: '待执行', tone: 'text-navy-400 bg-slate-900/40 border-white/5' },
  skipped: { label: '已跳过', tone: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
}

function DramaBasicFields({ drama }) {
  if (!drama) return null
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-4">
      {[
        ['创作轨道', drama.track_mode_display || drama.track_mode],
        ['当前阶段', drama.current_stage_display || drama.current_stage],
        ['完成度', drama.completion_rate != null ? `${drama.completion_rate}%` : '—'],
        ['交付状态', drama.delivery_status || '—'],
        ['已完成角色', `${(drama.completed_roles || []).length} 个`],
        ['Token 消耗', drama.total_tokens_used?.toLocaleString?.() ?? drama.total_tokens_used ?? '—'],
      ].map(([label, value]) => (
        <div key={label} className="rounded-xl border border-indigo-500/15 bg-indigo-500/5 px-3 py-2">
          <p className="text-[10px] text-indigo-300/70">{label}</p>
          <p className="text-sm text-white mt-0.5">{value ?? '—'}</p>
        </div>
      ))}
    </div>
  )
}

function DramaTracePanel({ dramaTrace, catalog }) {
  if (!dramaTrace) return null
  const phases = dramaTrace.phases || []
  const timeline = dramaTrace.timeline || []

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3 text-xs leading-relaxed text-indigo-200/90">
        <span className="font-medium text-indigo-100">Drama 36 角色轨</span>
        ：按部门顺序执行 drama.* 角色，产物写入 ProjectFusionArtifact，进度以 DramaProject 为 SSOT。
        {dramaTrace.track_plan?.label ? ` 当前计划：${dramaTrace.track_plan.label}。` : ''}
      </div>

      <DramaBasicFields drama={dramaTrace} />

      {phases.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {phases.map((phase) => (
            <div
              key={phase.phase}
              className={`rounded-xl border px-3 py-2 ${
                phase.is_complete
                  ? 'border-green-500/30 bg-green-500/5'
                  : 'border-white/5 bg-slate-900/40'
              }`}
            >
              <p className="text-[10px] text-navy-400">{phase.label}</p>
              <p className="text-sm text-white mt-0.5">
                {phase.completed_roles}/{phase.total_roles} 角色
              </p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3">
        <p className="text-sm text-navy-200 mb-2">角色执行时间线（最新 {timeline.length} 条）</p>
        {!timeline.length ? (
          <p className="text-sm text-navy-400 py-4 text-center">尚无角色执行记录</p>
        ) : (
          <div className="space-y-2 max-h-[520px] overflow-y-auto">
            {timeline.map((item) => {
              const cfg = DRAMA_EXEC_STATUS[item.status] || DRAMA_EXEC_STATUS.pending
              const name = resolveAgentDisplayName(item.agent_id, catalog)
              return (
                <div
                  key={item.execution_id}
                  className={`rounded-xl border px-4 py-3 ${cfg.tone}`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-white">{name}</span>
                    <span className="text-[10px] font-mono text-navy-400">{item.agent_id}</span>
                    <span className="ml-auto text-xs">{cfg.label}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-3 text-[10px] text-navy-400">
                    {item.total_tokens ? <span>{item.total_tokens} tokens</span> : null}
                    {item.elapsed_seconds != null ? (
                      <span>{item.elapsed_seconds.toFixed(1)}s</span>
                    ) : null}
                    {item.started_at ? (
                      <span>{new Date(item.started_at).toLocaleString()}</span>
                    ) : null}
                  </div>
                  {item.error_message ? (
                    <p className="mt-2 text-xs text-red-300/90 line-clamp-2">{item.error_message}</p>
                  ) : null}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function ProjectBasicPanel({ traceData }) {
  if (!traceData) return null
  return (
    <div className="sf-console-panel border border-white/5 p-5 space-y-4">
      {traceData.drama_trace ? <DramaBasicFields drama={traceData.drama_trace} /> : null}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
        {[
          ['题材', traceData.theme],
          ['创作入口', traceData.creation_entry],
          ['流水线模式', traceData.pipeline_mode],
          ['集数', traceData.episode_count],
          ['进度', traceData.progress_percent != null ? `${traceData.progress_percent}%` : '—'],
          ['评分', traceData.overall_score != null ? `${traceData.overall_score} · ${traceData.grade || ''}` : '—'],
          ['创建时间', traceData.created_at ? new Date(traceData.created_at).toLocaleString() : '—'],
          ['更新时间', traceData.updated_at ? new Date(traceData.updated_at).toLocaleString() : '—'],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2">
            <p className="text-[10px] text-navy-400">{label}</p>
            <p className="text-sm text-white mt-0.5">{value ?? '—'}</p>
          </div>
        ))}
      </div>
      {traceData.user_id ? (
        <Link
          to={`/admin/users?q=${encodeURIComponent(traceData.user_phone || traceData.user_id)}`}
          className="inline-flex text-sm text-gold-400 hover:text-gold-300"
        >
          查看所属用户 →
        </Link>
      ) : null}
    </div>
  )
}

function ProjectRunsPanel({ runs = [], catalog, onInspectRun }) {
  if (!runs.length) {
    return <p className="text-sm text-navy-400 py-8 text-center">暂无执行记录</p>
  }
  return (
    <div className="space-y-2">
      {runs.map((run) => (
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
  )
}

const ARTIFACT_LABELS = {
  project_brief: '项目 Brief',
  episode_scripts: '分集剧本',
  series_outline: '系列大纲',
  character_bible: '人物小传',
  structure_plan: '结构策划',
  adaptation_meta: '改编元数据',
}

function BriefArtifactCard({ item }) {
  return (
    <div className="rounded-xl border border-gold-500/20 bg-gold-500/5 p-4">
      <p className="text-sm font-medium text-gold-200">{ARTIFACT_LABELS.project_brief}</p>
      <dl className="mt-3 space-y-2 text-sm">
        <div>
          <dt className="text-[10px] text-navy-400">工作标题</dt>
          <dd className="text-white">{item.working_title || '—'}</dd>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <dt className="text-[10px] text-navy-400">题材</dt>
            <dd className="text-navy-200">{item.theme || '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] text-navy-400">集数</dt>
            <dd className="text-navy-200">{item.episode_count ?? '—'}</dd>
          </div>
        </div>
      </dl>
    </div>
  )
}

function ScriptsArtifactCard({ item }) {
  const titles = item.sample_titles || []
  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 md:col-span-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-cyan-200">{ARTIFACT_LABELS.episode_scripts}</p>
        <span className="text-xs text-navy-400">共 {item.episode_count ?? 0} 集</span>
      </div>
      {titles.length ? (
        <ul className="mt-3 space-y-1.5 text-sm text-navy-200">
          {titles.map((title, idx) => (
            <li key={`${title}-${idx}`} className="flex items-center gap-2">
              <span className="text-[10px] text-navy-500 w-5">{idx + 1}</span>
              <span className="truncate">{title}</span>
            </li>
          ))}
          {(item.episode_count ?? 0) > titles.length ? (
            <li className="text-xs text-navy-500 pl-7">… 另有 {item.episode_count - titles.length} 集</li>
          ) : null}
        </ul>
      ) : (
        <p className="mt-3 text-xs text-navy-400">暂无集标题摘要</p>
      )}
    </div>
  )
}

function GenericArtifactCard({ item }) {
  const label = ARTIFACT_LABELS[item.artifact_key] || item.artifact_key
  const entries = Object.entries(item).filter(([key]) => key !== 'artifact_key')
  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/40 p-4">
      <p className="text-sm font-medium text-white">{label}</p>
      <dl className="mt-2 space-y-1 text-xs text-navy-300">
        {entries.map(([key, value]) => (
          <div key={key} className="flex gap-2">
            <dt className="text-navy-500 shrink-0">{key}</dt>
            <dd className="text-navy-200 break-all">
              {Array.isArray(value) ? value.join('、') : String(value ?? '—')}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function ProjectArtifactsPanel({ artifacts = [] }) {
  if (!artifacts.length) {
    return <p className="text-sm text-navy-400 py-8 text-center">暂无 AI 产物</p>
  }
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {artifacts.map((item) => {
        if (item.artifact_key === 'project_brief') {
          return <BriefArtifactCard key={item.artifact_key} item={item} />
        }
        if (item.artifact_key === 'episode_scripts') {
          return <ScriptsArtifactCard key={item.artifact_key} item={item} />
        }
        return <GenericArtifactCard key={item.artifact_key} item={item} />
      })}
    </div>
  )
}

function ProjectQualityPanel({ defects = [] }) {
  if (!defects.length) {
    return <p className="text-sm text-navy-400 py-8 text-center">暂无质量缺陷记录</p>
  }
  return (
    <div className="space-y-2">
      {defects.map((row) => (
        <div key={row.id} className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-white font-medium">{row.dimension}</span>
            <span className="text-navy-400">· {row.defect_type}</span>
            {row.episode != null ? <span className="text-navy-500">第 {row.episode} 集</span> : null}
            <span className="ml-auto text-xs text-navy-400">{row.status_label || row.status}</span>
          </div>
          {row.details && typeof row.details === 'object' ? (
            <p className="text-xs text-navy-300 mt-2">
              {(row.details.message || row.details.summary || JSON.stringify(row.details)).slice(0, 240)}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  )
}

const TRACE_TABS = [
  { key: 'basic', label: '基本信息', icon: Info },
  { key: 'runs', label: '执行记录', icon: Layers },
  { key: 'artifacts', label: 'AI 产物', icon: Package },
  { key: 'quality', label: '质量缺陷', icon: AlertTriangle },
  { key: 'timeline', label: '执行轨迹', icon: GitBranch },
  { key: 'verify', label: '原创复核', icon: ShieldCheck },
]

export function useProjectTrace(projectId) {
  const [catalog, setCatalog] = useState(null)
  const [traceData, setTraceData] = useState(null)
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
      const [cat, traces] = await Promise.all([
        admin.agentCatalog().catch(() => null),
        admin.agentProjectTraces(id),
      ])
      setCatalog(cat)
      setTraceData(traces)
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

  return { catalog, traceData, loading, error, reload: load }
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
      <div className="max-h-[85vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-900/95 p-5 shadow-2xl">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">执行详情</h3>
            {detail ? (
              <p className="text-sm text-gold-400/90 mt-1">
                {resolveAgentDisplayName(detail.agent_id, catalog, detail.node_index)}
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
              <p className="text-sm text-gold-400 mb-2">LLM 用量汇总</p>
              <p className="text-xs text-navy-400 mb-3">
                {detail.llm_summary?.call_count ?? 0} 次 ·{' '}
                {(detail.llm_summary?.total_tokens ?? 0).toLocaleString()} Token
              </p>
              {(detail.llm_usage || []).length ? (
                <ul className="space-y-1 text-xs">
                  {detail.llm_usage.map((row) => (
                    <li
                      key={row.id}
                      className="flex flex-wrap justify-between gap-2 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2 text-navy-200"
                    >
                      <span>
                        {row.sub_skill_id || row.source_key || '—'} · {row.model_name}
                      </span>
                      <span className="text-navy-400">
                        入 {row.prompt_tokens ?? 0} / 出 {row.completion_tokens ?? 0}
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

/** 完整项目监察视图：摘要 + 多 Tab 穿透 */
export function ProjectAgentTraceView({
  projectId,
  compact = false,
  activeTab = 'basic',
  onTabChange,
  showSummary = true,
}) {
  const { catalog, traceData, loading, error } = useProjectTrace(projectId)
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

  const dramaRuns = (traceData.execution_runs || []).filter(
    (run) => String(run.agent_id || '').startsWith('drama.'),
  )

  return (
    <div className="space-y-4">
      <RunDetailModal runId={inspectRunId} onClose={() => setInspectRunId('')} />
      {showSummary ? (
        <ProjectOpsSummary
          data={traceData}
          compact={compact}
          onTabChange={onTabChange}
          onInspectRun={setInspectRunId}
        />
      ) : null}

      {!compact && onTabChange ? (
        <AdminTabBar tabs={TRACE_TABS} active={tab} onChange={onTabChange} />
      ) : null}

      {tab === 'basic' && !compact ? <ProjectBasicPanel traceData={traceData} /> : null}

      {tab === 'timeline' || compact ? (
        traceData.drama_trace ? (
          <DramaTracePanel dramaTrace={traceData.drama_trace} catalog={catalog} />
        ) : (
          <div className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-8 text-center text-sm text-navy-400">
            暂无 Drama 执行轨迹。请在 C 端工作台执行 drama.* 角色。
          </div>
        )
      ) : null}

      {tab === 'runs' && !compact ? (
        <ProjectRunsPanel
          runs={dramaRuns}
          catalog={catalog}
          onInspectRun={setInspectRunId}
        />
      ) : null}

      {tab === 'artifacts' && !compact ? (
        <ProjectArtifactsPanel artifacts={traceData.artifacts || []} />
      ) : null}

      {tab === 'quality' && !compact ? (
        <ProjectQualityPanel defects={traceData.quality_defects || []} />
      ) : null}

      {tab === 'verify' && !compact ? (
        <ProjectVerifyPanel summary={traceData.verify_summary} />
      ) : null}
    </div>
  )
}

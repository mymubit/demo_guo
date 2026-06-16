import { useCallback, useEffect, useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, Loader2, Play, X } from 'lucide-react'
import { admin } from '@/services/api'
import { cn } from '@/utils/cn'
import SubSkillStepBar from '@/components/admin/SubSkillStepBar'
import OrchestrationNodeStateBadge from '@/components/admin/OrchestrationNodeStateBadge'
import { agentIdToNodeId } from '@/utils/orchestrationNodeStates'

function formatTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

function runStatusToNodeState(status) {
  if (status === 'running') return 'running'
  if (status === 'failed') return 'failed'
  if (status === 'completed' || status === 'partial') return 'completed'
  return 'idle'
}

/** 执行回放：逐步高亮 Run 子技能，并支持跳转编排节点 */
export default function OrchestrationReplayPanel({
  runId,
  steps = [],
  onClose,
  onLocateNode,
  onOpenFlow,
}) {
  const [loading, setLoading] = useState(true)
  const [run, setRun] = useState(null)
  const [error, setError] = useState(null)
  const [cursor, setCursor] = useState(0)

  const load = useCallback(async () => {
    if (!runId) return
    setLoading(true)
    setError(null)
    try {
      const detail = await admin.agentExecutionRun(runId)
      setRun(detail)
      setCursor(0)
    } catch (err) {
      setError(err)
      setRun(null)
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    load()
  }, [load])

  const subSkills = run?.sub_skills || []
  const activeSkill = subSkills[cursor] || null
  const fusionNodeId = useMemo(() => {
    if (run?.fusion_node_id) return run.fusion_node_id
    if (run?.node_index != null) {
      const hit = steps.find((s) => s.node_index === run.node_index)
      if (hit) return hit.node_id
    }
    return agentIdToNodeId(steps, run?.agent_id)
  }, [run, steps])

  const nodeState = runStatusToNodeState(run?.status)

  function handleLocate() {
    if (fusionNodeId) onLocateNode?.(fusionNodeId)
  }

  if (!runId) return null

  return (
    <div className="sf-console-panel overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-white/5">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            <Play className="w-4 h-4 text-gold-400" />
            执行回放
          </div>
          <p className="text-xs font-mono text-navy-300 mt-0.5 truncate">{runId}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg text-navy-400 hover:text-white hover:bg-white/[0.06]"
          aria-label="关闭回放"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-2 py-12 text-sm text-navy-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          加载执行详情…
        </div>
      ) : error ? (
        <p className="px-4 py-8 text-sm text-red-300">{error.message || '加载失败'}</p>
      ) : !run ? (
        <p className="px-4 py-8 text-sm text-navy-400">无回放数据</p>
      ) : (
        <div className="p-4 space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm text-white font-medium">{run.project_title || '项目'}</p>
              <p className="text-xs text-navy-400 mt-0.5">
                {run.agent_id} · {formatTime(run.started_at)}
                {run.duration_ms != null ? ` · ${run.duration_ms}ms` : ''}
              </p>
            </div>
            <OrchestrationNodeStateBadge state={nodeState} />
          </div>

          <div className="flex flex-wrap gap-2">
            {fusionNodeId ? (
              <button
                type="button"
                onClick={handleLocate}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gold-300 border border-gold-500/30 hover:bg-gold-500/10"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                在编排页定位节点
              </button>
            ) : null}
            {onOpenFlow ? (
              <button
                type="button"
                onClick={() => onOpenFlow(fusionNodeId)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 hover:bg-white/[0.06]"
              >
                打开流程编排
              </button>
            ) : null}
          </div>

          {subSkills.length > 0 ? (
            <>
              <SubSkillStepBar steps={subSkills} activeIndex={cursor} />
              <div className="flex items-center justify-between gap-3">
                <button
                  type="button"
                  disabled={cursor <= 0}
                  onClick={() => setCursor((v) => Math.max(0, v - 1))}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 disabled:opacity-40"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  上一步
                </button>
                <span className="text-xs text-navy-400">
                  {cursor + 1} / {subSkills.length}
                  {activeSkill?.id ? ` · ${activeSkill.id}` : ''}
                </span>
                <button
                  type="button"
                  disabled={cursor >= subSkills.length - 1}
                  onClick={() => setCursor((v) => Math.min(subSkills.length - 1, v + 1))}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-navy-200 border border-white/10 disabled:opacity-40"
                >
                  下一步
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
              {activeSkill ? (
                <div className="space-y-1 rounded-xl border border-white/5 bg-slate-900/40 p-3 text-xs text-navy-300">
                  <div>
                    状态：
                    <span
                      className={cn(
                        'ml-1',
                        activeSkill.status === 'executed' && 'text-green-300',
                        activeSkill.status === 'failed' && 'text-red-300',
                        activeSkill.status === 'skipped' && 'text-navy-400',
                      )}
                    >
                      {activeSkill.status}
                    </span>
                  </div>
                  {activeSkill.message ? <div>说明：{activeSkill.message}</div> : null}
                </div>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-navy-400">本次执行无子技能记录</p>
          )}
        </div>
      )}
    </div>
  )
}

import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

const FALLBACK_WORKSPACE = [
  { index: 1, label: '简报', id: 'brief' },
  { index: 2, label: '世界观', id: 'world' },
  { index: 3, label: '角色', id: 'character' },
  { index: 4, label: '大纲', id: 'outline' },
  { index: 5, label: '剧本', id: 'script' },
]

const FALLBACK_POST_CHAIN = [
  { id: 'review', label: '审查' },
  { id: 'polish', label: '润色' },
  { id: 'score', label: '评分' },
  { id: 'marketing', label: '营销' },
]

/**
 * 创作流水线示意：优先读 blueprint，无数据时回退硬编码。
 */
export default function CreationPipelineDiagram({ compact = false, linkTo, blueprint }) {
  const stepClass = compact
    ? 'px-2.5 py-1 rounded-lg text-[11px] bg-slate-800/60 border border-white/10 text-navy-200'
    : 'px-3 py-1.5 rounded-xl text-xs bg-slate-800/60 border border-white/10 text-navy-100'

  const workspaceSteps = blueprint?.workspace_steps?.length
    ? blueprint.workspace_steps.map((s) => ({
        index: s.node_index,
        label: s.agent_name_zh || s.display_name || s.node_id,
        id: s.agent_id || s.node_id,
      }))
    : FALLBACK_WORKSPACE

  const postAgents = blueprint?.catalog?.postScriptAgents || []
  const postLabelById = Object.fromEntries(
    postAgents.map((a) => [a.id, a.name_zh || a.name || a.id])
  )
  const postChain = blueprint?.post_script_chain?.length
    ? blueprint.post_script_chain.map((id) => ({
        id,
        label: postLabelById[id] || id,
      }))
    : FALLBACK_POST_CHAIN

  const tailSteps = blueprint?.pipeline_tail_steps?.length
    ? blueprint.pipeline_tail_steps.map((s) => ({
        index: s.node_index,
        label: s.agent_name_zh || s.display_name || s.node_id,
        id: s.agent_id || s.node_id,
      }))
    : []

  const content = (
    <div className={`space-y-2 ${compact ? '' : 'p-4 rounded-2xl border border-white/5 bg-slate-900/40'}`}>
      <div className={`flex flex-wrap items-center gap-1.5`}>
      {workspaceSteps.map((s, i) => (
        <span key={`ws-${s.id}-${i}`} className="flex items-center gap-1.5">
          <span className={stepClass}>
            <span className="text-gold-400/90 mr-1">{s.index ?? i + 1}</span>
            {s.label}
          </span>
          {i < workspaceSteps.length - 1 ? (
            <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
          ) : null}
        </span>
      ))}
      {postChain.length > 0 ? (
        <>
          <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
          <span className="flex flex-wrap items-center gap-1">
            <span className="text-[10px] text-navy-400 mr-1">后处理</span>
            {postChain.map((s, i) => (
              <span key={`${s.id}-${i}`} className="flex items-center gap-1">
                <span className={`${stepClass} text-navy-300 border-dashed`}>{s.label}</span>
                {i < postChain.length - 1 ? (
                  <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
                ) : null}
              </span>
            ))}
          </span>
        </>
      ) : null}
      </div>
      {tailSteps.length > 0 ? (
        <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
          <span className="text-violet-400/80">分步尾部</span>
          {tailSteps.map((s, i) => (
            <span key={`tail-${s.id}-${i}`} className="flex items-center gap-1">
              <span className={`${stepClass} border-violet-700/40 text-violet-200`}>
                <span className="opacity-70 mr-1">{s.index}</span>
                {s.label}
              </span>
              {i < tailSteps.length - 1 ? (
                <ArrowRight className="w-3 h-3 text-navy-500 shrink-0" />
              ) : null}
            </span>
          ))}
        </div>
      ) : null}
      {blueprint?.execution_plan?.stages?.some((s) => s.type === 'parallel') ? (
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-cyan-400/80 pt-1">
          <span>并行阶段</span>
          {blueprint.execution_plan.stages
            .filter((s) => s.type === 'parallel')
            .map((stage) => (
              <span
                key={stage.group_id || stage.label}
                className="px-2 py-0.5 rounded-md border border-cyan-500/25 bg-cyan-500/10"
              >
                {stage.label}
              </span>
            ))}
        </div>
      ) : null}
      {blueprint?.execution_plan?.has_branches ? (
        <div className="text-[11px] text-violet-400/80 pt-1">含条件分支路由</div>
      ) : null}
    </div>
  )

  if (linkTo) {
    return (
      <Link to={linkTo} className="block hover:ring-1 hover:ring-gold-500/20 rounded-2xl transition">
        {content}
      </Link>
    )
  }
  return content
}

export { FALLBACK_WORKSPACE as WORKSPACE, FALLBACK_POST_CHAIN as POST_CHAIN }

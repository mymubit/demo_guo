import { Link } from 'react-router-dom'
import { ArrowRight, MousePointerClick } from 'lucide-react'

const FALLBACK_WORKSPACE = [
  { index: 1, label: '简报', id: 'brief' },
  { index: 2, label: '结构', id: 'structure' },
  { index: 3, label: '角色', id: 'character' },
  { index: 4, label: '大纲', id: 'outline' },
  { index: 5, label: '剧本', id: 'script' },
]

const FALLBACK_POST_AGENTS = [
  { id: 'review', label: '质检' },
  { id: 'score', label: '评分' },
  { id: 'polish', label: '润色' },
  { id: 'marketing', label: '营销' },
  { id: 'insight', label: '洞察' },
]

function normalizePostAgents(blueprint) {
  const explicit = blueprint?.explicit_post_agents || blueprint?.catalog?.explicitPostAgents
  if (Array.isArray(explicit) && explicit.length) {
    return explicit.map((agent) => ({
      id: agent.id || agent.agent_id || agent,
      label: agent.name_zh || agent.name || agent.label || agent.id || agent.agent_id || agent,
    }))
  }
  return FALLBACK_POST_AGENTS
}

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

  const postAgents = normalizePostAgents(blueprint)

  const content = (
    <div className={`space-y-2 ${compact ? '' : 'p-4 rounded-2xl border border-white/5 bg-slate-900/40'}`}>
      <div className="flex flex-wrap items-center gap-1.5">
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
      </div>

      {postAgents.length > 0 ? (
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-navy-400">
          <MousePointerClick className="w-3 h-3 text-cyan-300" />
          <span>显式后处理</span>
          {postAgents.map((agent) => (
            <span
              key={`post-${agent.id}`}
              className="rounded-lg border border-dashed border-cyan-500/30 bg-cyan-500/5 px-2 py-0.5 text-cyan-100/90"
            >
              {agent.label}
            </span>
          ))}
        </div>
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

export { FALLBACK_WORKSPACE as WORKSPACE, FALLBACK_POST_AGENTS as POST_CHAIN }

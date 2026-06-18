import { Bot, MousePointerClick } from 'lucide-react'

export default function MainChainPostScriptPanel({ blueprint }) {
  const agentIds = blueprint?.explicit_post_agents || blueprint?.catalog?.explicitPostAgents || []
  const agents = blueprint?.catalog?.postScriptAgents || []
  const labelById = Object.fromEntries(agents.map((a) => [a.id, a.name_zh || a.name || a.id]))

  return (
    <section className="sf-console-panel border border-white/10 px-5 py-4">
      <div className="flex items-start gap-3">
        <Bot className="mt-0.5 h-4 w-4 shrink-0 text-gold-400" />
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-white">显式后处理 Agent</div>
          <p className="mt-1 text-xs leading-relaxed text-navy-400">
            主链只包含 5 步，剧本生成完成即项目完成。质检、评分、润色、营销和洞察不会自动排队，只能由用户在作品页主动触发。
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {agentIds.map((id) => (
              <span
                key={id}
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-navy-200"
              >
                <MousePointerClick className="h-3 w-3 text-gold-400/80" />
                {labelById[id] || id}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

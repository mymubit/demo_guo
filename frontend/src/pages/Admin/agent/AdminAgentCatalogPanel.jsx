import { useCallback, useEffect, useMemo, useState } from 'react'
import { Bot, RefreshCw, Sparkles } from 'lucide-react'
import { admin } from '@/services/api'
import { AdminEmpty, AdminLoading } from '@/components/admin/AdminUI'
import AdminAgentKindBadge from '@/components/admin/AdminAgentKindBadge'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import { cn } from '@/utils/cn'

function AgentCatalogCard({ kind, title, subtitle, meta, onClick }) {
  const clickable = Boolean(onClick)
  const Tag = clickable ? 'button' : 'div'

  return (
    <Tag
      type={clickable ? 'button' : undefined}
      onClick={onClick}
      className={cn(
        'block w-full text-left rounded-2xl border border-white/5 bg-slate-900/40 p-4 transition-all',
        clickable && 'hover:border-gold-500/25 hover:bg-white/[0.06] cursor-pointer sf-focus-ring',
      )}
    >
      <div className="mb-2">
        <AdminAgentKindBadge kind={kind} />
      </div>
      <h4 className="text-sm font-semibold text-white truncate">{title}</h4>
      {subtitle ? (
        <p className="text-xs font-mono text-navy-300 mt-1.5 truncate">{subtitle}</p>
      ) : null}
      {meta ? <p className="text-xs text-navy-300 mt-2">{meta}</p> : null}
    </Tag>
  )
}

/**
 * Agent 全景目录：流水线 + 填表 + 后处理，统一心智模型。
 */
export default function AdminAgentCatalogPanel({ onSelectFormAgent }) {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const [loading, setLoading] = useState(true)
  const [blueprint, setBlueprint] = useState(null)
  const [formAgents, setFormAgents] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [bp, prompts] = await Promise.all([
        admin.getOrchestrationFlowBlueprint(),
        admin.listAiFieldPrompts(),
      ])
      setBlueprint(bp)
      setFormAgents(Array.isArray(prompts) ? prompts : [])
    } catch (err) {
      showMessage(err.message || '加载 Agent 目录失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showMessage])

  useEffect(() => {
    load()
  }, [load])

  const pipelineSteps = useMemo(() => {
    const steps = blueprint?.steps || []
    return [...steps].sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0))
  }, [blueprint])

  const postAgents = useMemo(() => {
    const chain = blueprint?.post_script_chain || []
    const agents = blueprint?.agents || {}
    return chain.map((agentId) => {
      const def = agents[agentId] || {}
      return {
        id: agentId,
        name: def.name_zh || def.name || agentId,
      }
    })
  }, [blueprint])

  const stats = useMemo(
    () => ({
      pipeline: pipelineSteps.filter((s) => s.enabled !== false).length,
      form: formAgents.filter((a) => a.is_active !== false).length,
      post: postAgents.length,
    }),
    [pipelineSteps, formAgents, postAgents],
  )

  if (loading && !blueprint) {
    return <AdminLoading label="加载 Agent 全景…" />
  }

  return (
    <div className="space-y-5">
      <MessageBanner />

      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-medium text-white flex items-center gap-2">
          <Bot className="w-4 h-4 text-gold-400" />
          Agent 目录
        </h3>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.06] disabled:opacity-60"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="sf-console-panel-subtle px-3 py-2.5 text-center">
          <div className="text-xl font-bold text-purple-200">{stats.pipeline}</div>
          <div className="text-[11px] text-navy-400">流水线</div>
        </div>
        <div className="sf-console-panel-subtle px-3 py-2.5 text-center">
          <div className="text-xl font-bold text-cyan-200">{stats.form}</div>
          <div className="text-[11px] text-navy-400">填表</div>
        </div>
        <div className="sf-console-panel-subtle px-3 py-2.5 text-center">
          <div className="text-xl font-bold text-amber-200">{stats.post}</div>
          <div className="text-[11px] text-navy-400">后处理</div>
        </div>
      </div>

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-navy-200">流水线 Agent</h3>
        {pipelineSteps.length === 0 ? (
          <AdminEmpty title="暂无流水线步骤" description="请在调度中心 · 流程编排同步 SSOT" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {pipelineSteps.map((step) => (
              <AgentCatalogCard
                key={step.node_id}
                kind="pipeline"
                title={step.agent_name_zh || step.display_name || step.node_id}
                subtitle={step.agent_id || step.fusion_node_id}
                meta={`步骤 ${step.chain_order ?? step.node_index} · ${step.coin_cost ?? 0} 币`}
              />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-navy-200 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          填表 Agent
        </h3>
        {formAgents.length === 0 ? (
          <AdminEmpty title="暂无填表 Agent" description="请切换至「填表 Agent」Tab 导入默认值" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {formAgents.map((row) => (
              <AgentCatalogCard
                key={row.action_key}
                kind="form"
                title={row.display_name || row.action_key}
                subtitle={row.action_key}
                meta={row.is_active === false ? '已停用' : '创作页字段按钮'}
                onClick={() => onSelectFormAgent?.(row.action_key)}
              />
            ))}
          </div>
        )}
      </section>

      {postAgents.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-medium text-navy-200">后处理 Agent</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {postAgents.map((agent) => (
              <AgentCatalogCard
                key={agent.id}
                kind="post"
                title={agent.name}
                subtitle={agent.id}
                meta="剧本完成后的可选链"
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}

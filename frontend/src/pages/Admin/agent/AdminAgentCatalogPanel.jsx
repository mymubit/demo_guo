import { useCallback, useEffect, useMemo, useState } from 'react'
import { Bot, MousePointerClick, RefreshCw, Sparkles } from 'lucide-react'
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
      {subtitle ? <p className="text-xs font-mono text-navy-300 mt-1.5 truncate">{subtitle}</p> : null}
      {meta ? <p className="text-xs text-navy-300 mt-2">{meta}</p> : null}
    </Tag>
  )
}

function normalizeExplicitPostAgents(catalog) {
  const explicit = catalog?.explicitPostAgents
  if (Array.isArray(explicit) && explicit.length) return explicit
  const catalogAgents = catalog?.postScriptAgents
  if (Array.isArray(catalogAgents) && catalogAgents.length) {
    return catalogAgents.map((agent) => agent.id || agent.agent_id || String(agent))
  }
  return []
}

export default function AdminAgentCatalogPanel({ onSelectFormAgent }) {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const [loading, setLoading] = useState(true)
  const [catalog, setCatalog] = useState(null)
  const [formAgents, setFormAgents] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [cat, prompts] = await Promise.all([
        admin.agentCatalog(),
        admin.listAiFieldPrompts(),
      ])
      setCatalog(cat)
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
    const steps = catalog?.workspaceAgents || []
    return [...steps].sort(
      (a, b) => (a.workspace_index ?? 0) - (b.workspace_index ?? 0),
    )
  }, [catalog])

  const postAgents = useMemo(() => {
    const explicitIds = normalizeExplicitPostAgents(catalog)
    const byId = Object.fromEntries(
      (catalog?.postScriptAgents || []).map((agent) => [agent.id, agent]),
    )
    return explicitIds.map((agentId, index) => {
      const agent = byId[agentId] || { id: agentId }
      return {
        id: agent.id || agentId,
        chainIndex: index,
        name: agent.name_zh || agent.name || agent.label || agent.id || agentId,
      }
    })
  }, [catalog])

  const stats = useMemo(
    () => ({
      pipeline: pipelineSteps.length,
      form: formAgents.filter((a) => a.is_active !== false).length,
      post: postAgents.length,
    }),
    [pipelineSteps, formAgents, postAgents],
  )

  if (loading && !catalog) {
    return <AdminLoading label="加载 Agent 目录..." />
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
          <div className="text-[11px] text-navy-400">主链</div>
        </div>
        <div className="sf-console-panel-subtle px-3 py-2.5 text-center">
          <div className="text-xl font-bold text-cyan-200">{stats.form}</div>
          <div className="text-[11px] text-navy-400">填表</div>
        </div>
        <div className="sf-console-panel-subtle px-3 py-2.5 text-center">
          <div className="text-xl font-bold text-amber-200">{stats.post}</div>
          <div className="text-[11px] text-navy-400">显式后处理</div>
        </div>
      </div>

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-navy-200">ScriptForge 主链 Agent</h3>
        {pipelineSteps.length === 0 ? (
          <AdminEmpty title="暂无主链步骤" description="请检查 Agent 注册表是否已写入 registry v2。" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {pipelineSteps.map((step) => (
              <AgentCatalogCard
                key={step.id || step.workspace_index}
                kind="pipeline"
                title={step.name_zh || step.name || step.id}
                subtitle={step.id}
                meta={`步骤 ${step.workspace_index ?? '—'} · ${step.sub_skill_count ?? 0} 个子技能`}
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
          <AdminEmpty title="暂无填表 Agent" description="可在填表 Agent 页签中导入或配置。" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {formAgents.map((row) => (
              <AgentCatalogCard
                key={row.action_key}
                kind="form"
                title={row.display_name || row.action_key}
                subtitle={row.action_key}
                meta={row.is_active === false ? '已停用' : '用户填表时主动触发'}
                onClick={() => onSelectFormAgent?.(row.action_key)}
              />
            ))}
          </div>
        )}
      </section>

      {postAgents.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-medium text-navy-200 flex items-center gap-2">
            <MousePointerClick className="w-3.5 h-3.5 text-amber-300" />
            显式后处理 Agent
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {postAgents.map((agent) => (
              <AgentCatalogCard
                key={`post-${agent.id}-${agent.chainIndex}`}
                kind="post"
                title={agent.name}
                subtitle={agent.id}
                meta="仅由用户在作品页主动触发，不参与主链完成态。"
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}

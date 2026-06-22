import { useCallback, useEffect, useMemo, useState } from 'react'
import { Bot, RefreshCw } from 'lucide-react'
import { admin } from '@/services/api'
import { AdminEmpty, AdminLoading } from '@/components/admin/AdminUI'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import { resolveAgentDisplayName } from '@/utils/agentExecutionLabels'

const DEPT_LABELS = {
  strategy: '战略选题部',
  worldbuilding: '世界构建部',
  plot_engine: '剧情引擎部',
  writing: '创作执行部',
  review: '评审质控部',
  polish: '修改润色部',
  production: '制作宣发部',
  ops: '合规总编室',
}

function RoleCard({ role }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/40 p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-semibold text-white">{role.name_zh || role.name}</h4>
        {role.is_fast_track ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">快速</span>
        ) : null}
      </div>
      <p className="text-xs font-mono text-navy-400 truncate">{role.id || role.agent_id}</p>
      {role.description ? (
        <p className="text-xs text-navy-300 mt-2 line-clamp-2">{role.description}</p>
      ) : null}
      <p className="text-[10px] text-navy-500 mt-2">顺序 {role.workspace_order ?? '—'}</p>
    </div>
  )
}

/** Drama 36 角色目录 — Admin Agent 页 */
export default function AdminAgentCatalogPanel() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const [loading, setLoading] = useState(true)
  const [catalog, setCatalog] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const cat = await admin.agentCatalog()
      setCatalog(cat)
    } catch (err) {
      showMessage(err.message || '加载 Drama 角色目录失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showMessage])

  useEffect(() => {
    load()
  }, [load])

  const departments = useMemo(() => {
    const depts = catalog?.departments || []
    if (depts.length) return depts
    const agents = catalog?.workspaceAgents || catalog?.agents || []
    const byDept = {}
    for (const agent of agents) {
      const dept = agent.dept || 'other'
      if (!byDept[dept]) {
        byDept[dept] = { dept_code: dept, dept_name: DEPT_LABELS[dept] || dept, roles: [] }
      }
      byDept[dept].roles.push({
        ...agent,
        id: agent.id || agent.agent_id,
        name_zh: agent.name_zh || resolveAgentDisplayName(agent.id, catalog),
      })
    }
    return Object.values(byDept)
  }, [catalog])

  const stats = useMemo(() => {
    const agents = catalog?.workspaceAgents || catalog?.agents || []
    return {
      total: agents.length,
      fast: (catalog?.fastTrackAgents || []).length,
      depts: departments.length,
    }
  }, [catalog, departments])

  if (loading && !catalog) {
    return <AdminLoading label="加载 Drama 角色目录..." />
  }

  return (
    <div className="space-y-5">
      <MessageBanner />

      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <Bot className="w-4 h-4 text-gold-400" />
            Drama 角色目录
          </h3>
          <p className="text-xs text-navy-400 mt-1">
            {stats.total} 个角色 · {stats.depts} 个部门 · 快速通道 {stats.fast} 个
          </p>
        </div>
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

      {!departments.length ? (
        <AdminEmpty title="暂无 Drama 角色" description="请运行 seed_drama_skills 初始化角色。" />
      ) : (
        departments.map((dept) => (
          <section key={dept.dept_code} className="space-y-3">
            <h3 className="text-sm font-medium text-navy-200">
              {dept.dept_name || DEPT_LABELS[dept.dept_code] || dept.dept_code}
              <span className="text-navy-500 font-normal ml-2">({dept.roles?.length || 0})</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {(dept.roles || []).map((role) => (
                <RoleCard key={role.id || role.agent_id} role={role} />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  )
}

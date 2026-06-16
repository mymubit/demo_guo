import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Layers, BarChart3 } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { AdminPageHeader, AdminPillTabs } from '@/components/admin/AdminUI'
import OrchestrationFlowPage from './OrchestrationFlowPage'
import OrchestrationMonitorPanel from './OrchestrationMonitorPanel'
import { OrchestrationHubContext } from './OrchestrationHubContext'
import { useOrchestrationHub } from '@/hooks/useOrchestrationHub'

const HUB_TABS = [
  { key: 'flow', label: '流程编排', icon: Layers },
  { key: 'monitor', label: '运行监察', icon: BarChart3 },
]

/** 调度中心 — 流程编排 / 运行监察共享联动状态 */
export default function OrchestrationHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'flow'
  const [steps, setSteps] = useState([])

  const hub = useOrchestrationHub(steps)

  const contextValue = useMemo(
    () => ({
      ...hub,
      steps,
      setSteps,
    }),
    [hub, steps],
  )

  const switchTab = (key) => {
    const next = new URLSearchParams(searchParams)
    next.set('tab', key)
    setSearchParams(next, { replace: true })
  }

  const headerMeta =
    tab === 'monitor'
      ? {
          crumb: '运行监察',
          title: '调度执行监控',
          subtitle: '子技能执行健康度 · 近期 Run 回放与节点定位',
        }
      : {
          crumb: '流程编排',
          title: '主链蓝图 · Fusion 节点包',
          subtitle: '7 节点主链 · 流水线步骤与 Prompt',
        }

  return (
    <OrchestrationHubContext.Provider value={contextValue}>
      <AdminShell hideDescription>
        <AdminPageHeader
          crumbs={[{ label: 'Console' }, { label: headerMeta.crumb }]}
          title={headerMeta.title}
          subtitle={headerMeta.subtitle}
        />
        <AdminPillTabs tabs={HUB_TABS} active={tab} onChange={switchTab} />
        {tab === 'monitor' ? <OrchestrationMonitorPanel /> : <OrchestrationFlowPage />}
      </AdminShell>
    </OrchestrationHubContext.Provider>
  )
}

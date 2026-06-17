import { Toaster } from 'sonner'
import { useEffect } from 'react'
import AppRoutes from '@/router'
import { GlobalRequestLoading } from '@/components/ui'
import { MonitorRouteTracker } from '@/utils/monitor'
import { useConfigStore } from '@/services/config/configStore'
import { installBehaviorTracker } from '@/utils/behaviorTracker'

function ConfigBootstrap() {
  const fetchPublicConfigs = useConfigStore((state) => state.fetchPublicConfigs)

  useEffect(() => {
    fetchPublicConfigs()
  }, [fetchPublicConfigs])

  return null
}

function BehaviorTrackerBootstrap() {
  useEffect(() => {
    // 【运营 F1】自动挂载 6 个核心埋点（landing_view 在此触发）
    installBehaviorTracker()
  }, [])
  return null
}

export default function App() {
  return (
    <>
      <ConfigBootstrap />
      <BehaviorTrackerBootstrap />
      <Toaster
        position="top-center"
        closeButton
        offset={20}
        toastOptions={{
          duration: 4200,
          classNames: {
            toast: 'sf-toast',
            title: 'text-sm font-semibold text-white',
            description: 'text-xs text-navy-300',
            actionButton: 'bg-gold-400 text-navy-950 hover:bg-gold-300',
            cancelButton: 'bg-slate-800 text-navy-200 hover:bg-slate-700',
            closeButton: 'border-white/10 bg-slate-900 text-navy-300 hover:text-white',
            success: 'border-success-500/35',
            error: 'border-danger-500/35',
            warning: 'border-warning-500/35',
            info: 'border-info-500/35',
          },
        }}
      />
      <GlobalRequestLoading />
      <MonitorRouteTracker />
      <AppRoutes />
    </>
  )
}

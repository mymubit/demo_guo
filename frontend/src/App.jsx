import { Toaster } from 'sonner'
import 'sonner/dist/styles.css'
import { useEffect } from 'react'
import AppRoutes from '@/router'
import { GlobalRequestLoading } from '@/components/ui'
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
        theme="dark"
        position="top-center"
        closeButton
        offset={20}
        toastOptions={{
          duration: 4200,
          classNames: {
            toast: 'sf-toast',
            title: 'sf-toast-title',
            description: 'sf-toast-description',
            actionButton: 'bg-gold-400 text-navy-950 hover:bg-gold-300',
            cancelButton: 'bg-navy-800 text-slate-300 hover:bg-navy-700',
            closeButton: 'sf-toast-close',
            success: 'sf-toast-success',
            error: 'sf-toast-error',
            warning: 'sf-toast-warning',
            info: 'sf-toast-info',
          },
        }}
      />
      <GlobalRequestLoading />
      <AppRoutes />
    </>
  )
}

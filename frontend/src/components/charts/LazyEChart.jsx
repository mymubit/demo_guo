import { lazy, Suspense } from 'react'
import { PageLoading } from '@/components/ui'

const EChartImpl = lazy(() => import('./EChart'))

/** 懒加载 ECharts，避免非图表路由打入 echarts chunk */
export default function LazyEChart(props) {
  return (
    <Suspense fallback={<PageLoading className="min-h-0" label="图表加载中…" />}>
      <EChartImpl {...props} />
    </Suspense>
  )
}

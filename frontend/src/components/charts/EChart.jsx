import { useEffect, useMemo, useRef } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import { ensureEchartsRegistered, echarts, SCRIPTFORGE_CHART_THEME } from './register'
import { EmptyState, ErrorState, PageLoading } from '@/components/ui'
import { cn } from '@/utils/cn'

ensureEchartsRegistered()

/**
 * 通用 ECharts 容器：自动 resize、深色主题、notMerge 防止旧数据残留。
 */
export default function EChart({
  option,
  height = 280,
  minWidth = 0,
  className = '',
  loading = false,
  error,
  emptyText = '暂无数据',
  onEvents,
  notMerge = true,
  lazyUpdate = true,
  visibilityKey,
}) {
  const chartRef = useRef(null)
  const style = useMemo(
    () => ({ height: typeof height === 'number' ? `${height}px` : height, minWidth }),
    [height, minWidth],
  )

  useEffect(() => {
    const chart = chartRef.current?.getEchartsInstance?.()
    const chartDom = chart?.getDom?.()
    if (!chart || !chartDom) return undefined

    const handleResize = () => chart.resize()
    const observer =
      typeof ResizeObserver !== 'undefined'
        ? new ResizeObserver(handleResize)
        : null

    observer?.observe(chartDom)
    window.addEventListener('orientationchange', handleResize)
    window.addEventListener('resize', handleResize)
    window.setTimeout(handleResize, 0)

    return () => {
      observer?.disconnect()
      window.removeEventListener('orientationchange', handleResize)
      window.removeEventListener('resize', handleResize)
    }
  }, [option, visibilityKey])

  if (loading) {
    return <PageLoading className={cn('min-h-0', className)} label="图表加载中…" />
  }

  if (error) {
    return <ErrorState title="图表加载失败" description={error.message || String(error)} className={className} />
  }

  if (!option) {
    return <EmptyState compact title={emptyText} description="请调整筛选条件或稍后再试" className={className} />
  }

  return (
    <div className="w-full overflow-x-auto overscroll-x-contain">
      <ReactEChartsCore
        ref={chartRef}
        echarts={echarts}
        option={option}
        theme={SCRIPTFORGE_CHART_THEME}
        style={style}
        className={className}
        notMerge={notMerge}
        lazyUpdate={lazyUpdate}
        showLoading={false}
        onEvents={onEvents}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}

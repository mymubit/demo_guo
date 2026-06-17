import { useEffect, useMemo, useRef } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import { ensureEchartsRegistered, echarts, SCRIPTFORGE_CHART_THEME } from './register'
import { EmptyState, ErrorState, PageLoading } from '@/components/ui'
import { cn } from '@/utils/cn'

function isLiveChart(chart) {
  return chart && typeof chart.isDisposed === 'function' && !chart.isDisposed()
}

function safeResize(chartRef) {
  const chart = chartRef.current?.getEchartsInstance?.()
  if (!isLiveChart(chart)) return
  try {
    chart.resize({ silent: true })
  } catch {
    // dispose 与 resize 竞态时忽略
  }
}

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
  const containerRef = useRef(null)
  const style = useMemo(
    () => ({ height: typeof height === 'number' ? `${height}px` : height, minWidth }),
    [height, minWidth],
  )
  const isChartMounted = Boolean(option) && !loading && !error

  // ResizeObserver / 窗口监听仅在图表挂载时创建一次，不随 option 变化重建
  useEffect(() => {
    if (!isChartMounted) return undefined

    let observer = null
    let cancelled = false
    let attachTimer = 0
    let resizeFrame = 0

    const handleResize = () => {
      if (cancelled) return
      if (resizeFrame) window.cancelAnimationFrame(resizeFrame)
      resizeFrame = window.requestAnimationFrame(() => {
        resizeFrame = 0
        if (!cancelled) safeResize(chartRef)
      })
    }

    const attach = () => {
      if (cancelled) return
      const chart = chartRef.current?.getEchartsInstance?.()
      const container = containerRef.current
      if (!isLiveChart(chart) || !container) {
        attachTimer = window.setTimeout(attach, 16)
        return
      }

      observer =
        typeof ResizeObserver !== 'undefined'
          ? new ResizeObserver(handleResize)
          : null

      observer?.observe(container)
      window.addEventListener('orientationchange', handleResize)
      window.addEventListener('resize', handleResize)
      handleResize()
    }

    attach()

    return () => {
      cancelled = true
      if (attachTimer) window.clearTimeout(attachTimer)
      observer?.disconnect()
      if (resizeFrame) window.cancelAnimationFrame(resizeFrame)
      window.removeEventListener('orientationchange', handleResize)
      window.removeEventListener('resize', handleResize)
    }
  }, [isChartMounted])

  // Tab 切换等 visibility 变化时仅触发 resize，不重建 observer
  useEffect(() => {
    if (!isChartMounted) return undefined
    const frame = window.requestAnimationFrame(() => safeResize(chartRef))
    return () => window.cancelAnimationFrame(frame)
  }, [visibilityKey, isChartMounted])

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
    <div ref={containerRef} className="w-full overflow-x-auto overscroll-x-contain">
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
        autoResize={false}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}

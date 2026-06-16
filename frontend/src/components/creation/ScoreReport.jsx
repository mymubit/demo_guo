import { useMemo } from 'react'
import { EChart, buildHorizontalBarOption } from '@/components/charts'

/** 8 维评分展示（ECharts 横向条 + 综合分） */
export default function ScoreReport({ report, className = '' }) {
  const dimensions = report?.dimensions || []
  const overall = report?.overallScore ?? report?.overall_score
  const grade = report?.grade || '—'

  const option = useMemo(() => {
    if (!dimensions.length) return null
    return buildHorizontalBarOption({
      rows: dimensions.map((d) => ({
        display_name: d.label || d.key,
        call_count: Number(d.rawScore ?? 0),
      })),
      valueKey: 'call_count',
      valueSuffix: ' 分',
      color: '#d4a853',
      maxItems: 12,
    })
  }, [dimensions])

  if (!report) return null

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-navy-200">综合评分</span>
        <span className="text-2xl font-bold gradient-text">
          {overall != null ? overall : '—'}
          <span className="text-sm text-navy-400 ml-2">{grade}</span>
        </span>
      </div>
      {option ? (
        <EChart option={option} height={Math.max(200, dimensions.length * 36)} />
      ) : (
        dimensions.map((dim) => {
          const raw = dim.rawScore ?? 0
          const pct = Math.min(100, Math.max(0, Number(raw) || 0))
          return (
            <div key={dim.key} className="flex items-center gap-3 text-sm">
              <span className="w-24 text-navy-300 flex-shrink-0">{dim.label}</span>
              <div className="flex-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="w-10 text-right text-gold-400 font-semibold">{raw ?? '—'}</span>
            </div>
          )
        })
      )}
      {report.releasePassScore != null && (
        <p className="text-xs text-navy-400 text-center">
          系统放行线：{report.releasePassScore} 分
        </p>
      )}
    </div>
  )
}
